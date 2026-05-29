"""Пауза и возобновление напоминаний в чате."""

from __future__ import annotations

from aiogram import Bot

from bot.db.repository import async_session, get_active_chat_reminders, set_chat_paused
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
        if reminder.next_run_at:
            schedule_reminder(bot, reminder.id, reminder.next_run_at)
            count += 1
    return count
