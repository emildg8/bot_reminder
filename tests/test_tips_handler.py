import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.db.repository import get_or_create_user
from bot.handlers.tips import cmd_subscribe_redirect, cmd_thanks, send_thanks_screen
from bot.services.stars_tips import format_thanks_screen, tip_keyboard


@pytest.mark.asyncio
async def test_cmd_thanks_when_enabled(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    message = MagicMock()
    message.from_user.id = 70001
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_thanks(message)
    message.answer.assert_awaited_once()
    text = message.answer.await_args[0][0]
    assert "Благодарность" in text
    assert message.answer.await_args.kwargs["reply_markup"] == tip_keyboard()


@pytest.mark.asyncio
async def test_cmd_subscribe_shows_redirect_note(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 70002
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    user.is_pro = True
    await patched_db.commit()
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_subscribe_redirect(message)
    text = message.answer.await_args[0][0]
    assert "подписк" in text.lower()


@pytest.mark.asyncio
async def test_cmd_subscribe_new_user_no_pro_note(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 70003
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_subscribe_redirect(message)
    text = message.answer.await_args[0][0]
    assert "pro" not in text.lower()


@pytest.mark.asyncio
async def test_cmd_thanks_when_disabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    message = MagicMock()
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_thanks(message)
    assert "недоступна" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_subscribe_disabled_mentions_no_subscription(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    message = MagicMock()
    message.chat.id = 1
    message.answer = AsyncMock()
    await send_thanks_screen(message, subscribe_redirect=True)
    assert "subscribe" in message.answer.await_args[0][0].lower()


def test_thanks_screen_mentions_free():
    assert "бесплат" in format_thanks_screen().lower()


def test_thanks_screen_shows_custom_amount_hint():
    text = format_thanks_screen()
    assert "свою" in text.lower()


def test_thanks_screen_shows_prior_tips():
    text = format_thanks_screen(prior_tips=(2, 150))
    assert "150" in text
    assert "2" in text
