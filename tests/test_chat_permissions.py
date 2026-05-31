from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatMemberStatus

from bot.services.chat_permissions import (
    bot_can_post_reminders,
    can_manage_group_reminders,
    format_bot_cannot_post_hint,
)


def _member(status: ChatMemberStatus, **kwargs):
    return SimpleNamespace(status=status, **kwargs)


@pytest.mark.asyncio
async def test_bot_can_post_private_chat():
    bot = AsyncMock()
    assert await bot_can_post_reminders(bot, 12345) is True
    bot.get_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_bot_can_post_member_ok():
    bot = AsyncMock()
    bot.get_me.return_value = SimpleNamespace(id=99)
    bot.get_chat_member.return_value = _member(ChatMemberStatus.MEMBER)
    assert await bot_can_post_reminders(bot, -100123) is True


@pytest.mark.asyncio
async def test_bot_can_post_admin_without_send():
    bot = AsyncMock()
    bot.get_me.return_value = SimpleNamespace(id=99)
    bot.get_chat_member.return_value = _member(
        ChatMemberStatus.ADMINISTRATOR,
        can_post_messages=False,
        can_send_messages=False,
    )
    assert await bot_can_post_reminders(bot, -100123) is False


@pytest.mark.asyncio
async def test_bot_can_post_api_error_fail_closed():
    bot = AsyncMock()
    bot.get_me.return_value = SimpleNamespace(id=99)
    bot.get_chat_member.side_effect = RuntimeError("network")
    assert await bot_can_post_reminders(bot, -100123) is False


@pytest.mark.asyncio
async def test_can_manage_private():
    bot = AsyncMock()
    assert await can_manage_group_reminders(bot, 42, 1) is True


@pytest.mark.asyncio
async def test_can_manage_group_admin():
    bot = AsyncMock()
    bot.get_chat_member.return_value = _member(ChatMemberStatus.ADMINISTRATOR)
    assert await can_manage_group_reminders(bot, -100, 555) is True


@pytest.mark.asyncio
async def test_can_manage_group_member_denied():
    bot = AsyncMock()
    bot.get_chat_member.return_value = _member(ChatMemberStatus.MEMBER)
    assert await can_manage_group_reminders(bot, -100, 555) is False


def test_cannot_post_hint():
    assert "Отправка сообщений" in format_bot_cannot_post_hint()
