"""Часовой пояс: личка — user, collective — chat_settings."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.repository import get_or_create_chat, get_or_create_user
from bot.services.chat_ctx import is_group_chat

__all__ = ["get_effective_timezone", "is_group_chat"]


async def get_effective_timezone(
    session: AsyncSession,
    chat_id: int,
    user_telegram_id: int,
) -> str:
    if is_group_chat(chat_id):
        chat = await get_or_create_chat(session, chat_id, settings.default_timezone)
        return chat.timezone
    user = await get_or_create_user(session, user_telegram_id, settings.default_timezone)
    return user.timezone
