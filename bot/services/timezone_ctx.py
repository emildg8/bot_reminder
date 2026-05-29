"""Часовой пояс: личка — user, группа — chat_settings."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.repository import get_or_create_chat, get_or_create_user


def is_group_chat(chat_id: int) -> bool:
    return chat_id < 0


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
