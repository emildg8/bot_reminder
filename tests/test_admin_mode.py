import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers.admin import btn_admin_mode, cb_adminmode, cmd_adminmode
from bot.handlers.health import cmd_health, cmd_ping
from bot.keyboards.reply import admin_mode_button_text, menu_keyboard_for_user
from bot.services.admin_access import (
    format_bot_admin_denied,
    is_admin_listed,
    is_bot_admin,
    set_admin_tools_cached,
)
from bot.services.help_display import format_help_for_chat
from bot.texts.messages import format_admin_help_footer, format_ping_admin_suffix
from tests.callback_helpers import make_bot, make_callback, make_message


def test_is_admin_listed_and_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    assert is_admin_listed(42) is True
    assert is_admin_listed(1) is False
    assert is_bot_admin(42) is True
    set_admin_tools_cached(42, False)
    assert is_bot_admin(42) is False
    set_admin_tools_cached(42, True)
    assert is_bot_admin(42) is True


def test_format_bot_admin_denied_user_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    set_admin_tools_cached(42, False)
    text = format_bot_admin_denied(42)
    assert "режим пользователя" in text.lower()
    assert "/adminmode" in text


def test_admin_mode_reply_button_label(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    set_admin_tools_cached(42, True)
    assert "пользовател" in admin_mode_button_text(admin_tools=True).lower()
    set_admin_tools_cached(42, False)
    assert "админ" in admin_mode_button_text(admin_tools=False).lower()


def test_menu_keyboard_has_admin_row_for_listed(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    set_admin_tools_cached(42, True)
    kb = menu_keyboard_for_user(42)
    labels = [btn.text for row in kb.keyboard for btn in row]
    assert any("пользовател" in t.lower() for t in labels)


@pytest.mark.asyncio
async def test_adminmode_requires_listed_admin(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [99])
    message = make_message(1)
    message.text = "/adminmode"
    await cmd_adminmode(message, make_bot())
    assert "администратор" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_adminmode_switch_to_user(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [50])
    set_admin_tools_cached(50, True)

    async def _set(_session, telegram_id: int, enabled: bool) -> None:
        set_admin_tools_cached(telegram_id, enabled)

    monkeypatch.setattr("bot.services.admin_mode.set_admin_tools_enabled", _set)
    monkeypatch.setattr("bot.services.admin_mode.sync_admin_command_menu", AsyncMock())
    message = make_message(50)
    message.text = "/adminmode user"
    await cmd_adminmode(message, make_bot())
    assert message.answer.await_count >= 1
    assert is_bot_admin(50) is False


@pytest.mark.asyncio
async def test_reply_button_toggles_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [52])
    set_admin_tools_cached(52, True)

    async def _set(_session, telegram_id: int, enabled: bool) -> None:
        set_admin_tools_cached(telegram_id, enabled)

    monkeypatch.setattr("bot.services.admin_mode.set_admin_tools_enabled", _set)
    monkeypatch.setattr("bot.services.admin_mode.sync_admin_command_menu", AsyncMock())
    message = make_message(52)
    message.text = admin_mode_button_text(admin_tools=True)
    await btn_admin_mode(message, make_bot())
    assert is_bot_admin(52) is False


@pytest.mark.asyncio
async def test_adminmode_callback_to_admin(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [51])
    set_admin_tools_cached(51, False)

    async def _set(_session, telegram_id: int, enabled: bool) -> None:
        set_admin_tools_cached(telegram_id, enabled)

    monkeypatch.setattr("bot.services.admin_mode.set_admin_tools_enabled", _set)
    monkeypatch.setattr("bot.services.admin_mode.sync_admin_command_menu", AsyncMock())
    cb = make_callback("adminmode:admin", 51)
    cb.message.edit_text = AsyncMock()
    cb.message.chat.id = 51
    await cb_adminmode(cb, make_bot())
    assert is_bot_admin(51) is True
    cb.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_health_denied_in_user_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [53])
    set_admin_tools_cached(53, False)
    message = make_message(53)
    await cmd_health(message, make_bot())
    body = message.answer.await_args[0][0]
    assert "режим пользователя" in body.lower()


@pytest.mark.asyncio
async def test_ping_shows_admin_suffix(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [54])
    set_admin_tools_cached(54, True)
    message = make_message(54)
    await cmd_ping(message)
    assert "admin" in message.answer.await_args[0][0]


def test_help_footer_and_ping_suffix():
    assert "администратора" in format_admin_help_footer(admin_tools=True)
    assert "пользователя" in format_admin_help_footer(admin_tools=False)
    assert "user-test" in format_ping_admin_suffix(admin_tools=False)


def test_help_for_listed_admin(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [55])
    set_admin_tools_cached(55, False)
    chat = MagicMock()
    chat.type = "private"
    chat.id = 55
    text = format_help_for_chat(chat, 55)
    assert "Админ бота" in text
    assert "пользователя" in text
