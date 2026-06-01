from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.db.repository import create_reminder, get_or_create_user
from bot.handlers.create import handle_text
from bot.handlers.health import cmd_health, cmd_ping
from bot.handlers.manage import clear_confirm, cmd_clear
from bot.handlers.search import cmd_search
from tests.callback_helpers import make_bot, make_callback, make_message, patch_create_flow, patch_scheduler
from tests.db_helpers import patched_db


async def _seed_reminder(session, user_id: int, text: str = "активное"):
    user = await get_or_create_user(session, user_id, "Europe/Moscow")
    return await create_reminder(
        session,
        user_id=user.id,
        chat_id=user_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text=text,
        kind="once",
        next_run_at=datetime(2030, 4, 1, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )


@pytest.mark.asyncio
async def test_handle_text_creates_confirm_draft(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    patch_create_flow(monkeypatch)
    user_id = 9400
    message = make_message(user_id)
    message.text = "через 30 минут выпить воды"

    await handle_text(message, make_bot())

    message.answer.assert_awaited()
    body = message.answer.await_args[0][0]
    assert "воды" in body or "30" in body
    markup = message.answer.await_args.kwargs.get("reply_markup")
    assert markup is not None


@pytest.mark.asyncio
async def test_cmd_search_with_query(patched_db):
    user_id = 9401
    await _seed_reminder(patched_db, user_id, "найти таблетки")
    message = make_message(user_id)
    message.text = "/search таблет"

    await cmd_search(message)

    body = message.answer.await_args[0][0]
    assert "Найдено" in body


@pytest.mark.asyncio
async def test_cmd_search_without_query(patched_db):
    message = make_message(9402)
    message.text = "/search"

    await cmd_search(message)

    assert "/search" in message.answer.await_args[0][0]


@pytest.mark.asyncio
async def test_cmd_ping(patched_db):
    message = make_message(9403)

    await cmd_ping(message)

    body = message.answer.await_args[0][0]
    assert "работает" in body.lower()
    assert "v3." in body


@pytest.mark.asyncio
async def test_cmd_health_requires_admin(patched_db, monkeypatch):
    message = make_message(9404)
    monkeypatch.setattr("bot.handlers.health.is_bot_admin", lambda _uid: False)

    await cmd_health(message, make_bot())

    assert "администратор" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_cmd_clear_shows_confirm(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9405
    await _seed_reminder(patched_db, user_id)
    message = make_message(user_id)
    message.text = "/clear"

    await cmd_clear(message, make_bot())

    body = message.answer.await_args[0][0]
    assert "Удалить все" in body


@pytest.mark.asyncio
async def test_clear_yes_deactivates(patched_db, monkeypatch):
    scheduled = patch_scheduler(monkeypatch)
    user_id = 9406
    await _seed_reminder(patched_db, user_id, "удалить все")
    callback = make_callback("clear:yes", user_id)

    await clear_confirm(callback, make_bot())

    body = callback.message.edit_text.await_args[0][0]
    assert "Удалено" in body
