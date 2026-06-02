"""Сбор данных для /status — единая логика для command и menu."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from bot.db.repository import async_session, count_user_star_tips, get_active_chat_reminders, is_chat_paused
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, is_collective_chat, tz_scope_label
from bot.services.chat_delivery import resolve_delivery_chat_id
from bot.services.chat_permissions import bot_can_post_reminders
from bot.services.admin_access import is_admin_listed, is_bot_admin
from bot.services.status_info import format_next_reminder_line
from bot.services.stars_tips import tips_enabled
from bot.services.timezone_ctx import get_effective_timezone
from bot.texts.messages import format_admin_mode_line, format_developer_status_line, format_status
from bot.version import __version__


async def build_status_text(bot: Bot, message: Message) -> str:
    kind = chat_kind_from_chat(message.chat)
    async with async_session() as session:
        delivery_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )
        reminders = await get_active_chat_reminders(session, delivery_id)
        paused = await is_chat_paused(session, delivery_id)
        tz = await get_effective_timezone(session, delivery_id, message.from_user.id)
        tip_stats = None
        if kind == ChatKind.PRIVATE and message.from_user:
            tip_stats = await count_user_star_tips(session, message.from_user.id)

    next_line = format_next_reminder_line(reminders, tz)
    delivery_line = None
    if delivery_id != message.chat.id:
        delivery_line = "📢 Доставка: <b>в связанный канал</b>"

    post_ok = None
    if is_collective_chat(message.chat.id):
        post_ok = await bot_can_post_reminders(bot, delivery_id)

    admin_mode_line = None
    if kind == ChatKind.PRIVATE and is_admin_listed(message.from_user.id):
        admin_mode_line = format_admin_mode_line(admin_tools=is_bot_admin(message.from_user.id))

    tips_line = None
    if kind == ChatKind.PRIVATE:
        if tip_stats and tip_stats[0] > 0:
            _, total = tip_stats
            tips_line = f"⭐ Ты поддержал: <b>{total}</b> ⭐ · ещё: /thanks"
        elif tips_enabled():
            tips_line = "⭐ Поддержать автора: /thanks"

    author_line = None
    if kind == ChatKind.PRIVATE:
        author_line = format_developer_status_line(version=__version__)

    return format_status(
        count=len(reminders),
        paused=paused,
        tz=tz,
        tz_scope=tz_scope_label(kind),
        version=__version__,
        chat_kind=kind,
        next_line=next_line,
        delivery_line=delivery_line,
        post_ok=post_ok,
        admin_mode_line=admin_mode_line,
        tips_line=tips_line,
        author_line=author_line,
    )
