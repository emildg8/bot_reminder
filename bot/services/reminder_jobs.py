"""Отмена задач APScheduler и Telegram scheduled posts."""

from __future__ import annotations

from datetime import datetime

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder
from bot.db.repository import async_session, get_reminder
from bot.services.channel_schedule import (
    cancel_reminder_telegram_schedule,
    setup_channel_telegram_schedule,
)
from bot.services.scheduler import schedule_reminder, scheduler


def cancel_reminder_job(reminder_id: int) -> bool:
    job_id = f"reminder_{reminder_id}"
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    scheduler.remove_job(job_id)
    return True


async def teardown_reminder_schedule(
    bot: Bot,
    session: AsyncSession,
    reminder: Reminder,
) -> None:
    cancel_reminder_job(reminder.id)
    await cancel_reminder_telegram_schedule(bot, session, reminder)


async def refresh_reminder_schedule(
    bot: Bot,
    session: AsyncSession,
    reminder: Reminder,
    *,
    reschedule_job,
) -> None:
    """APScheduler job + optional Telegram scheduled post для канала."""
    reschedule_job()
    await setup_channel_telegram_schedule(bot, session, reminder)


async def schedule_reminder_with_channel(
    bot: Bot,
    reminder_id: int,
    run_at: datetime,
    *,
    timezone: str = "Europe/Moscow",
) -> None:
    schedule_reminder(bot, reminder_id, run_at, timezone=timezone)
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is not None:
            await setup_channel_telegram_schedule(bot, session, reminder)
