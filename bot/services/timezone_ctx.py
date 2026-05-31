"""Часовой пояс: личка — user, collective — chat_settings."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.repository import find_channel_by_linked_chat, get_or_create_chat, get_or_create_user
from bot.services.chat_ctx import is_group_chat


async def collective_ops_chat_id(
    session: AsyncSession,
    chat_id: int,
    chat_type: str | None = None,
) -> int:
    """Чат для TZ / pause / reminders — канал, если это discussion group."""
    if not is_group_chat(chat_id):
        return chat_id
    if chat_type is not None:
        from bot.services.chat_delivery import resolve_delivery_chat_id

        return await resolve_delivery_chat_id(session, chat_id, chat_type)
    linked = await find_channel_by_linked_chat(session, chat_id)
    return linked if linked is not None else chat_id


async def get_effective_timezone(
    session: AsyncSession,
    chat_id: int,
    user_telegram_id: int,
    *,
    chat_type: str | None = None,
) -> str:
    if is_group_chat(chat_id):
        ops_id = await collective_ops_chat_id(session, chat_id, chat_type)
        chat = await get_or_create_chat(session, ops_id, settings.default_timezone)
        return chat.timezone
    user = await get_or_create_user(session, user_telegram_id, settings.default_timezone)
    return user.timezone
