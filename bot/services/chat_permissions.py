"""Права на управление напоминаниями в группах."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from bot.config import settings
from bot.services.chat_ctx import is_group_chat

logger = logging.getLogger(__name__)


async def bot_can_post_reminders(bot: Bot, chat_id: int) -> bool:
    """Может ли бот отправлять сообщения в collective-чат."""
    if not is_group_chat(chat_id):
        return True
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
    except Exception as exc:
        logger.warning("Cannot check bot member in %s: %s", chat_id, exc)
        return False

    if member.status == ChatMemberStatus.ADMINISTRATOR:
        can = getattr(member, "can_post_messages", None)
        if can is None:
            can = getattr(member, "can_send_messages", None)
        return True if can is None else bool(can)
    if member.status == ChatMemberStatus.RESTRICTED:
        return bool(getattr(member, "can_send_messages", False))
    return member.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.CREATOR,
    )


def format_bot_cannot_post_hint() -> str:
    return (
        "⚠️ <b>Бот не может писать в этот чат</b> — напоминание не дойдёт.\n"
        "Дай боту право «Отправка сообщений» или сделай админом."
    )


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
