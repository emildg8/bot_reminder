"""Пауза и возобновление напоминаний в чате."""

from __future__ import annotations

from datetime import datetime

from aiogram import Bot
from zoneinfo import ZoneInfo

from bot.db.repository import (
    async_session,
    get_active_chat_reminders,
    get_reminder,
    set_chat_paused,
    update_reminder_next_run,
)
from bot.services.reminder_utils import resolve_next_run_on_resume
from bot.services.scheduler import schedule_reminder, scheduler


async def pause_chat_reminders(bot: Bot, chat_id: int) -> int:
    async with async_session() as session:
        await set_chat_paused(session, chat_id, True)
        reminders = await get_active_chat_reminders(session, chat_id)

    for reminder in reminders:
        job_id = f"reminder_{reminder.id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    return len(reminders)


async def resume_chat_reminders(bot: Bot, chat_id: int) -> int:
    async with async_session() as session:
        await set_chat_paused(session, chat_id, False)
        reminders = await get_active_chat_reminders(session, chat_id)

    count = 0
    for reminder in reminders:
        tz = ZoneInfo(reminder.timezone)
        now = datetime.now(tz)
        next_run = resolve_next_run_on_resume(reminder, now)
        if next_run is None:
            continue

        if next_run != reminder.next_run_at:
            async with async_session() as session:
                db_reminder = await get_reminder(session, reminder.id)
                if db_reminder is not None:
                    await update_reminder_next_run(session, db_reminder, next_run)

        schedule_reminder(bot, reminder.id, next_run, timezone=reminder.timezone)
        count += 1
    return count
