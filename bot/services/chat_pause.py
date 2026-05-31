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
from bot.services.channel_schedule import cancel_reminder_telegram_schedule
from bot.services.reminder_jobs import cancel_reminder_job, schedule_reminder_with_channel
from bot.services.reminder_utils import resolve_next_run_on_resume


async def pause_chat_reminders(bot: Bot, chat_id: int) -> int:
    async with async_session() as session:
        await set_chat_paused(session, chat_id, True)
        reminders = await get_active_chat_reminders(session, chat_id)

    for reminder in reminders:
        cancel_reminder_job(reminder.id)
        async with async_session() as session:
            db_reminder = await get_reminder(session, reminder.id)
            if db_reminder is not None:
                await cancel_reminder_telegram_schedule(bot, session, db_reminder)

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

        await schedule_reminder_with_channel(
            bot, reminder.id, next_run, timezone=reminder.timezone
        )
        count += 1
    return count
