"""Права на управление напоминаниями в группах."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config import settings
from bot.services.timezone_ctx import is_group_chat

logger = logging.getLogger(__name__)


async def can_manage_group_reminders(bot: Bot, chat_id: int, user_id: int) -> bool:
    """В личке — всегда да. В группе — админ чата или bot admin."""
    if not is_group_chat(chat_id):
        return True
    if user_id in settings.admin_telegram_ids:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR)
    except Exception as exc:
        logger.warning("Cannot check chat member %s in %s: %s", user_id, chat_id, exc)
        return False
