import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers.tips import cmd_thanks
from bot.services.stars_tips import format_thanks_screen, tip_keyboard


@pytest.mark.asyncio
async def test_cmd_thanks_when_enabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    message = MagicMock()
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_thanks(message)
    message.answer.assert_awaited_once()
    text = message.answer.await_args[0][0]
    assert "Благодарность" in text
    assert message.answer.await_args.kwargs["reply_markup"] == tip_keyboard()


@pytest.mark.asyncio
async def test_cmd_thanks_when_disabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    message = MagicMock()
    message.chat.id = 1
    message.answer = AsyncMock()
    await cmd_thanks(message)
    assert "недоступна" in message.answer.await_args[0][0].lower()


def test_thanks_screen_mentions_free():
    assert "бесплат" in format_thanks_screen().lower()
