"""Куда доставлять напоминание: канал, linked discussion group, обычная группа."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatType
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repository import (
    find_channel_by_linked_chat,
    get_or_create_chat,
    update_channel_linked_chat,
)
from bot.services.chat_ctx import ChatKind, chat_kind_from_type

logger = logging.getLogger(__name__)


async def sync_channel_linked_chat(
    bot: Bot,
    session: AsyncSession,
    channel_id: int,
    *,
    default_timezone: str,
) -> int | None:
    """Сохраняет linked_chat_id канала (группа обсуждений)."""
    try:
        chat = await bot.get_chat(channel_id)
    except Exception as exc:
        logger.warning("Cannot get channel %s: %s", channel_id, exc)
        return None

    linked_id = getattr(chat, "linked_chat_id", None)
    if not linked_id:
        return None

    await get_or_create_chat(session, channel_id, default_timezone)
    await update_channel_linked_chat(session, channel_id, linked_id)
    logger.info("Channel %s linked to discussion %s", channel_id, linked_id)
    return linked_id


async def resolve_delivery_chat_id(
    session: AsyncSession,
    source_chat_id: int,
    chat_type: str | ChatType | None,
) -> int:
    """Discussion group → родительский канал; иначе исходный чат."""
    kind = chat_kind_from_type(chat_type)
    if kind == ChatKind.CHANNEL:
        return source_chat_id

    parent = await find_channel_by_linked_chat(session, source_chat_id)
    if parent is not None:
        return parent
    return source_chat_id
