from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType

from bot.db.repository import get_or_create_user
from bot.handlers.create import cmd_remind
from bot.handlers.group_menu import gmenu_legacy
from tests.callback_helpers import make_bot, make_callback, patch_create_flow, patch_scheduler


def _group_message(user_id: int, text: str) -> MagicMock:
    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.username = "tester"
    message.chat.id = -100123456
    message.chat.type = ChatType.SUPERGROUP
    message.chat.title = "Test Group"
    message.text = text
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_gmenu_list_sends_active_list(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9500
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    callback = make_callback("gmenu:list", user_id, chat_id=-100123456)
    callback.message.chat.type = ChatType.SUPERGROUP

    await gmenu_legacy(callback)

    callback.message.answer.assert_awaited()


@pytest.mark.asyncio
async def test_gmenu_legacy_dismisses_other(patched_db):
    callback = make_callback("gmenu:home", 9501, chat_id=-100123456)
    callback.message.chat.type = ChatType.SUPERGROUP
    callback.message.edit_reply_markup = AsyncMock()

    await gmenu_legacy(callback)

    callback.answer.assert_awaited()


@pytest.mark.asyncio
async def test_cmd_remind_group_stores_draft(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    patch_create_flow(monkeypatch)
    collective_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("bot.handlers.create.send_collective_confirm", collective_mock)
    user_id = 9502
    message = _group_message(user_id, "/remind@bot через 30 минут созвон")
    command = MagicMock()
    command.args = "через 30 минут созвон"

    await cmd_remind(message, command, make_bot())

    collective_mock.assert_awaited()


@pytest.mark.asyncio
async def test_cmd_remind_group_resolves_user_mention(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    patch_create_flow(monkeypatch)
    stored: dict = {}

    def capture_draft(*args, **kwargs):
        stored.update(kwargs)
        return "draft-mention"

    monkeypatch.setattr("bot.handlers.create.store_draft", capture_draft)
    monkeypatch.setattr("bot.handlers.create.parse_all_reminders", AsyncMock(return_value=[MagicMock()]))
    monkeypatch.setattr(
        "bot.handlers.create.format_batch_parsed_summary_html",
        lambda *a, **k: "summary",
    )
    monkeypatch.setattr("bot.handlers.create.send_collective_confirm", AsyncMock(return_value=True))
    resolve = AsyncMock(return_value=4242)
    monkeypatch.setattr("bot.handlers.create.resolve_mention_user_id", resolve)
    monkeypatch.setattr("bot.handlers.create.offer_ambiguous_time_choice", AsyncMock(return_value=False))
    monkeypatch.setattr("bot.handlers.create.bot_can_post_reminders", AsyncMock(return_value=True))

    user_id = 9503
    message = _group_message(user_id, "/remind@bot @alice через 30 минут созвон")
    message.entities = [
        SimpleNamespace(
            type="text_mention",
            offset=12,
            length=6,
            user=SimpleNamespace(id=4242, username="alice", is_bot=False),
        ),
    ]
    command = MagicMock()
    command.args = "@alice через 30 минут созвон"

    await cmd_remind(message, command, make_bot(username="bot", bot_id=1))

    resolve.assert_awaited()
    assert stored.get("mention_telegram_id") == 4242
    assert stored.get("mention_provided") is True


@pytest.mark.asyncio
async def test_cmd_remind_reply_assigns_target(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    stored: dict = {}

    monkeypatch.setattr(
        "bot.handlers.create.store_draft",
        lambda *a, **kw: stored.update(kw) or "draft-reply",
    )
    monkeypatch.setattr("bot.handlers.create.parse_all_reminders", AsyncMock(return_value=[MagicMock()]))
    monkeypatch.setattr(
        "bot.handlers.create.format_batch_parsed_summary_html",
        lambda *a, **k: "summary",
    )
    monkeypatch.setattr("bot.handlers.create.send_collective_confirm", AsyncMock(return_value=True))
    monkeypatch.setattr("bot.handlers.create.resolve_mention_user_id", AsyncMock(return_value=7777))
    monkeypatch.setattr("bot.handlers.create.offer_ambiguous_time_choice", AsyncMock(return_value=False))
    monkeypatch.setattr("bot.handlers.create.bot_can_post_reminders", AsyncMock(return_value=True))

    user_id = 9504
    message = _group_message(user_id, "/remind@bot завтра созвон")
    message.entities = []
    message.reply_to_message = MagicMock()
    message.reply_to_message.from_user = SimpleNamespace(
        id=7777, username="target", is_bot=False
    )
    command = MagicMock()
    command.args = "завтра созвон"

    await cmd_remind(message, command, make_bot(username="bot", bot_id=1))

    assert stored.get("mention_telegram_id") == 7777
    assert stored.get("mention_provided") is True
