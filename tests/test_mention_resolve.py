from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatMemberStatus

from bot.services.mention_resolve import is_user_in_chat, resolve_mention_user_id


@pytest.mark.asyncio
async def test_resolve_without_chat_id():
    bot = AsyncMock()
    bot.get_chat = AsyncMock(return_value=MagicMock(id=42))
    uid = await resolve_mention_user_id(bot, None, "alice")
    assert uid == 42


@pytest.mark.asyncio
async def test_resolve_rejects_non_member():
    bot = AsyncMock()
    bot.get_chat = AsyncMock(return_value=MagicMock(id=42))
    member = MagicMock(status=ChatMemberStatus.LEFT)
    bot.get_chat_member = AsyncMock(return_value=member)
    uid = await resolve_mention_user_id(bot, None, "alice", chat_id=-100)
    assert uid is None


@pytest.mark.asyncio
async def test_resolve_accepts_member():
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status=ChatMemberStatus.MEMBER))
    uid = await resolve_mention_user_id(bot, 42, "alice", chat_id=-100)
    assert uid == 42


@pytest.mark.asyncio
async def test_is_user_in_chat():
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=MagicMock(status=ChatMemberStatus.MEMBER))
    assert await is_user_in_chat(bot, -100, 1) is True
