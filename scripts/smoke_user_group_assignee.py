#!/usr/bin/env python3
"""Smoke «как пользователь»: @бот + имя из списка в группе (без Telegram API).

Симулирует реальные entities и порядок роутеров tips → create.
Показывает тексты, которые пользователь увидит в группе и в личке.

Запуск: python scripts/smoke_user_group_assignee.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("BOT_TOKEN", "0:smoke-test-token")

from aiogram.enums import ChatType

import bot.db.repository as repository
from bot.db.models import Base
from bot.db.repository import get_or_create_user
from bot.handlers.create import cmd_remind, _handle_collective_phrase_message
from bot.handlers.health import cmd_ping
from bot.services.nlp.llm_parser import parse_all_reminders
from bot.services.telegram_format import format_reminder_message
from bot.version import __version__
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BOT_USERNAME = "break_remind_bot"
BOT_ID = 900001
GROUP_ID = -1001234567890
USER_ID = 111222333
ASSIGNEE_ID = 424242
ASSIGNEE_NAME = "Emil"


class _CaptureBot:
    """Записывает исходящие сообщения бота."""

    def __init__(self) -> None:
        self.out: list[dict] = []
        self._me = SimpleNamespace(username=BOT_USERNAME, id=BOT_ID, can_read_all_group_messages=True)

    async def get_me(self):
        return self._me

    async def send_message(self, chat_id, text, **kwargs):
        self.out.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_to": kwargs.get("reply_to_message_id"),
            }
        )
        msg = MagicMock()
        msg.message_id = 9000 + len(self.out)
        return msg


def _group_message(text: str, *, entities: list | None = None) -> MagicMock:
    message = MagicMock()
    message.message_id = 777
    message.text = text
    message.caption = None
    message.entities = entities or []
    message.caption_entities = []
    message.chat = MagicMock()
    message.chat.id = GROUP_ID
    message.chat.type = ChatType.SUPERGROUP
    message.chat.title = "Болталка"
    message.from_user = MagicMock()
    message.from_user.id = USER_ID
    message.from_user.username = "tester"
    message.from_user.is_bot = False
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    return message


def _entities_display_name() -> list:
    """Как при тапе @бот и Emil из списка (см. test_mention_from_message)."""
    return [
        SimpleNamespace(type="mention", offset=0, length=17),
        SimpleNamespace(
            type="text_mention",
            offset=18,
            length=4,
            user=SimpleNamespace(id=ASSIGNEE_ID, username=None, is_bot=False, first_name=ASSIGNEE_NAME),
        ),
    ]


def _safe_print(text: str) -> None:
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(text.encode(enc, errors="replace").decode(enc))


async def _setup_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()

    class _Shared:
        def __init__(self, s):
            self._s = s

        def __call__(self):
            return self

        async def __aenter__(self):
            return self._s

        async def __aexit__(self, *a):
            return None

    shared = _Shared(session)
    repository.engine = engine
    repository.async_session = shared
    for mod in (
        "bot.handlers.create",
        "bot.handlers.callbacks",
        "bot.handlers.menu",
        "bot.services.create_confirm",
        "bot.services.collective_confirm",
        "bot.services.chat_delivery",
        "bot.services.mention_resolve",
        "bot.services.timezone_ctx",
    ):
        try:
            __import__(mod)
        except ImportError:
            continue
        setattr(sys.modules[mod], "async_session", shared)

    async with shared() as s:
        await get_or_create_user(s, USER_ID, "Europe/Moscow")
    return engine, session


async def _run_scenario(name: str, message: MagicMock, bot: _CaptureBot) -> None:
    bot.out.clear()
    from bot.handlers.create import _handle_collective_phrase_message

    await _handle_collective_phrase_message(message, bot)
    _safe_print(f"\n=== {name} ===")
    if not bot.out:
        _safe_print("  [FAIL] Bot silent")
        return
    for i, item in enumerate(bot.out, 1):
        where = "group" if item["chat_id"] == GROUP_ID else "dm"
        reply = " (reply)" if item["reply_to"] else ""
        plain = item["text"].replace("<b>", "").replace("</b>", "")
        _safe_print(f"  [{i}] {where}{reply}: {plain[:220]}")


async def main() -> int:
    errors: list[str] = []
    _safe_print(f"smoke_user_group_assignee · repo v{__version__}")

    parsed = await parse_all_reminders("Через 1 минуту тест", "Europe/Moscow")
    if not parsed:
        errors.append("NLP: не распознано «Через 1 минуту тест»")
    else:
        _safe_print(f"NLP rules: OK · {parsed[0].kind} · delay={getattr(parsed[0], 'delay_seconds', None)}")

    engine, _session = await _setup_db()
    bot = _CaptureBot()

    # Патч resolve → assignee в группе
    import bot.handlers.create as create_mod
    import bot.services.create_confirm as confirm_mod
    async def _resolve(*a, **k):
        return ASSIGNEE_ID

    create_mod.resolve_mention_user_id = _resolve
    confirm_mod.bot_can_post_reminders = AsyncMock(return_value=True)

    import bot.services.reminder_create as rc

    rc.schedule_reminder = MagicMock()

    # 1) /ping в группе (как пользователь проверяет версию)
    ping_msg = _group_message("/ping")
    await cmd_ping(ping_msg, bot)
    _safe_print("\n=== /ping в группе ===")
    if ping_msg.answer.await_count:
        body = ping_msg.answer.await_args[0][0]
        _safe_print(f"  {body}")
        if "v3.46" not in body and __version__ not in body:
            errors.append("/ping: нет версии")
        if "Group Privacy" not in body:
            errors.append("/ping: нет строки Group Privacy в группе")
    else:
        errors.append("/ping: нет answer")

    # 2) @бот + Emil из списка (главный сценарий)
    text = f"@{BOT_USERNAME} {ASSIGNEE_NAME} Через 1 минуту тест"
    msg = _group_message(text, entities=_entities_display_name())
    await _run_scenario("User: @bot + Emil (from @ list) + 1 min", msg, bot)

    group_replies = [o for o in bot.out if o["chat_id"] == GROUP_ID]
    if not group_replies:
        errors.append("@бот+Emil: нет ответа в группе")
    else:
        gtext = group_replies[0]["text"]
        if "Emil" not in gtext and "👤" not in gtext:
            errors.append("@бот+Emil: preview без имени")
        if group_replies[0].get("reply_to") != 777:
            errors.append("@бот+Emil: нет reply на сообщение")

    # 3) /remind@бот (рабочий fallback)
    remind = _group_message(
        f"/remind@{BOT_USERNAME} {ASSIGNEE_NAME} Через 1 минуту тест",
        entities=_entities_display_name(),
    )
    command = MagicMock()
    command.args = f"{ASSIGNEE_NAME} Через 1 минуту тест"
    bot.out.clear()
    await cmd_remind(remind, command, bot)
    _safe_print("\n=== User: /remind@bot + Emil + 1 min ===")
    for i, item in enumerate(bot.out, 1):
        where = "group" if item["chat_id"] == GROUP_ID else "dm"
        reply = " (reply)" if item["reply_to"] else ""
        plain = item["text"].replace("<b>", "").replace("</b>", "")
        _safe_print(f"  [{i}] {where}{reply}: {plain[:220]}")
    if not [o for o in bot.out if o["chat_id"] == GROUP_ID]:
        errors.append("/remind@бот: нет ответа в группе")

    # 4) Emil (text_mention) не в чате + @alice, без времени → кнопки (P3 v3.46.4)
    async def _resolve_unresolved(*a, **k):
        return None

    from bot.services.nlp.schemas import ParsedReminder

    _orig_parse = create_mod.parse_all_reminders

    async def _parse_for_assignee_pick(phrase: str, timezone: str):
        if phrase.strip() == "созвон":
            return [ParsedReminder(text="созвон", kind="once", delay_seconds=3600)]
        return await _orig_parse(phrase, timezone)

    create_mod.resolve_mention_user_id = _resolve_unresolved
    create_mod.parse_all_reminders = _parse_for_assignee_pick
    plain_multi = _group_message(
        f"@{BOT_USERNAME} {ASSIGNEE_NAME} @alice созвон",
        entities=_entities_display_name()
        + [SimpleNamespace(type="mention", offset=23, length=6)],
    )
    bot.out.clear()
    await _handle_collective_phrase_message(plain_multi, bot)
    _safe_print("\n=== User: Emil not in chat + @alice, pick buttons ===")
    if plain_multi.answer.await_count:
        body = plain_multi.answer.await_args[0][0]
        _safe_print(f"  {body.replace('<b>', '').replace('</b>', '')[:240]}")
        if "Кому напомнить" not in body or ASSIGNEE_NAME not in body:
            errors.append("plain+@alice: нет подсказки выбора")
    else:
        errors.append("plain+@alice: нет answer (кнопки assignee)")
    create_mod.parse_all_reminders = _orig_parse
    create_mod.resolve_mention_user_id = _resolve

    # 5) Plain name без @ в фразе → preview Emil? в группе (resolve=None)
    plain_only = _group_message(f"@{BOT_USERNAME} {ASSIGNEE_NAME} Через 1 минуту тест")
    create_mod.resolve_mention_user_id = _resolve_unresolved
    bot.out.clear()
    await _handle_collective_phrase_message(plain_only, bot)
    create_mod.resolve_mention_user_id = _resolve
    _safe_print("\n=== User: typed Emil (no @ list), 1 min ===")
    g_only = [o for o in bot.out if o["chat_id"] == GROUP_ID]
    if not g_only:
        errors.append("plain only: нет ответа в группе")
    elif "?" not in g_only[0]["text"] and ASSIGNEE_NAME not in g_only[0]["text"]:
        errors.append("plain only: нет unresolved preview")
    else:
        _safe_print(f"  {g_only[0]['text'].replace('<b>', '').replace('</b>', '')[:220]}")

    # 6) Срабатывание (что увидит в группе после confirm)
    fired = format_reminder_message(
        "тест",
        mention_user_id=ASSIGNEE_ID,
        mention_username=ASSIGNEE_NAME,
        chat_id=GROUP_ID,
    )
    _safe_print("\n=== Срабатывание напоминания (в группе) ===")
    _safe_print(f"  {fired.replace('<b>', '').replace('</b>', '')}")
    if "участник" in fired and ASSIGNEE_NAME not in fired:
        errors.append("fire: «участник» вместо Emil")

    await _session.close()
    await engine.dispose()

    if errors:
        _safe_print("\nFAIL:")
        for e in errors:
            _safe_print(f"  - {e}")
        return 1
    _safe_print("\nsmoke_user_group_assignee OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
