import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers.admin import cmd_admin_panel, cmd_broadcast, cmd_grantpro, cmd_userinfo
from bot.services.admin_access import set_admin_tools_cached
from bot.services.admin_panel import (
    BroadcastFilter,
    format_broadcast_preview,
    parse_broadcast_message,
    parse_target_telegram_id,
    pop_pending_broadcast,
    send_broadcast_preview_to_admin,
)


@pytest.mark.asyncio
async def test_admin_panel_limited_in_user_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [70])
    set_admin_tools_cached(70, False)
    message = MagicMock()
    message.from_user.id = 70
    message.answer = AsyncMock()
    await cmd_admin_panel(message)
    body = message.answer.await_args[0][0]
    assert "режим пользователя" in body.lower()
    assert message.answer.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_admin_panel_opens(monkeypatch, patched_db):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [71])
    set_admin_tools_cached(71, True)
    message = MagicMock()
    message.from_user.id = 71
    message.answer = AsyncMock()
    await cmd_admin_panel(message)
    body = message.answer.await_args[0][0]
    assert "Панель администратора" in body
    assert "7 дней" in body


@pytest.mark.asyncio
async def test_userinfo_unknown(monkeypatch, patched_db):
    monkeypatch.setattr("bot.handlers.admin.is_bot_admin", lambda _u: True)
    message = MagicMock()
    message.from_user.id = 72
    message.text = "/userinfo 999999001"
    message.reply_to_message = None
    message.answer = AsyncMock()
    await cmd_userinfo(message)
    body = message.answer.await_args[0][0]
    assert "не найден" in body.lower()


@pytest.mark.asyncio
async def test_userinfo_from_reply(monkeypatch, patched_db):
    monkeypatch.setattr("bot.handlers.admin.is_bot_admin", lambda _u: True)
    message = MagicMock()
    message.from_user.id = 72
    message.text = "/userinfo"
    message.reply_to_message = MagicMock()
    message.reply_to_message.from_user = MagicMock()
    message.reply_to_message.from_user.id = 888002
    message.reply_to_message.from_user.is_bot = False
    message.answer = AsyncMock()
    assert parse_target_telegram_id(message) == 888002
    from bot.db.repository import get_or_create_user

    await get_or_create_user(patched_db, 888002, "Europe/Moscow")
    await cmd_userinfo(message)
    assert "888002" in message.answer.await_args[0][0]


@pytest.mark.asyncio
async def test_grantpro_from_reply(monkeypatch, patched_db):
    monkeypatch.setattr("bot.handlers.admin.is_bot_admin", lambda _u: True)
    monkeypatch.setattr("bot.handlers.admin.monetization_active", lambda: True)
    message = MagicMock()
    message.from_user.id = 72
    message.text = "/grantpro"
    message.reply_to_message = MagicMock()
    message.reply_to_message.from_user = MagicMock()
    message.reply_to_message.from_user.id = 888003
    message.reply_to_message.from_user.is_bot = False
    message.answer = AsyncMock()
    from bot.db.repository import get_or_create_user

    await get_or_create_user(patched_db, 888003, "Europe/Moscow")
    await cmd_grantpro(message)
    assert "888003" in message.answer.await_args[0][0]
    from bot.services.admin_audit import format_admin_log

    log_text = await format_admin_log()
    assert "grant Pro" in log_text


@pytest.mark.asyncio
async def test_broadcast_preview_flow(monkeypatch, patched_db):
    monkeypatch.setattr("bot.handlers.admin.is_bot_admin", lambda _u: True)
    message = MagicMock()
    message.from_user.id = 73
    message.text = "/broadcast активные Привет"
    message.answer = AsyncMock()
    await cmd_broadcast(message, MagicMock())
    body = message.answer.await_args[0][0]
    assert "Превью" in body
    assert "активными" in body
    pending = await pop_pending_broadcast(73)
    assert pending is not None
    assert pending.text == "Привет"
    assert pending.filter == BroadcastFilter.ACTIVE


@pytest.mark.asyncio
async def test_broadcast_test_to_self(monkeypatch):
    monkeypatch.setattr("bot.handlers.admin.is_bot_admin", lambda _u: True)
    bot = MagicMock()
    bot.send_message = AsyncMock()
    message = MagicMock()
    message.from_user.id = 74
    message.text = "/broadcast test Hello"
    message.answer = AsyncMock()
    await cmd_broadcast(message, bot)
    bot.send_message.assert_awaited_once()
    assert "себе" in message.answer.await_args[0][0].lower() or "Пример" in message.answer.await_args[0][0]


def test_parse_broadcast_active_filter():
    msg = MagicMock()
    msg.text = "/broadcast pro Скидка"
    parsed = parse_broadcast_message(msg)
    assert parsed is not None
    assert parsed.filter == BroadcastFilter.PRO
    assert parsed.text == "Скидка"


def test_format_broadcast_preview_truncates():
    long = "x" * 500
    text = format_broadcast_preview(long, 10, filter=BroadcastFilter.ALL)
    assert "…" in text


@pytest.mark.asyncio
async def test_send_broadcast_preview_to_admin():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    assert await send_broadcast_preview_to_admin(bot, 1, "hi") is True
