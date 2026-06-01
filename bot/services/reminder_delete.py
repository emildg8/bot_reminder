"""Удаление напоминания (команда и callback)."""

from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder, ReminderEventKind
from bot.db.repository import deactivate_reminder, get_reminder
from bot.services.reminder_history import log_reminder_event
from bot.services.reminder_jobs import teardown_reminder_schedule


async def delete_owned_reminder(
    bot: Bot,
    session: AsyncSession,
    reminder_id: int,
    user_telegram_id: int,
) -> tuple[str | None, Reminder | None]:
    """(error_text, reminder) — reminder только при успехе."""
    reminder = await get_reminder(session, reminder_id)
    if reminder is None or not reminder.is_active:
        return "Напоминание не найдено.", None
    if reminder.created_by_telegram_id != user_telegram_id:
        return "Можно удалять только свои напоминания.", None

    await teardown_reminder_schedule(bot, session, reminder)
    await deactivate_reminder(session, reminder)
    await log_reminder_event(
        session,
        reminder=reminder,
        chat_id=reminder.chat_id,
        user_telegram_id=user_telegram_id,
        text=reminder.text,
        kind=ReminderEventKind.DELETED,
    )
    return None, reminder
