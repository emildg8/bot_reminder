import logging
from datetime import datetime

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select

from bot.db.models import Reminder, User
from bot.db.repository import async_session, deactivate_reminder, get_reminder, update_reminder_next_run
from bot.keyboards.inline import reminder_actions_keyboard
from bot.services.reminder_utils import advance_reminder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_reminder(bot: Bot, reminder_id: int) -> None:
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            return

        result = await session.execute(select(User).where(User.id == reminder.user_id))
        user = result.scalar_one()

        await bot.send_message(
            chat_id=user.telegram_id,
            text=f"⏰ Напоминание: {reminder.text}",
            reply_markup=reminder_actions_keyboard(reminder.id),
        )

        next_run = advance_reminder(reminder, user.timezone)
        if next_run is None:
            await deactivate_reminder(session, reminder)
            job_id = f"reminder_{reminder_id}"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
        else:
            await update_reminder_next_run(session, reminder, next_run)
            schedule_reminder(bot, reminder.id, next_run)


def schedule_reminder(bot: Bot, reminder_id: int, run_at: datetime) -> None:
    job_id = f"reminder_{reminder_id}"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=run_at),
        id=job_id,
        args=[bot, reminder_id],
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled reminder %s at %s", reminder_id, run_at.isoformat())


async def restore_scheduled_reminders(bot: Bot) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Reminder).where(Reminder.is_active.is_(True), Reminder.next_run_at.is_not(None))
        )
        reminders = list(result.scalars().all())

    now = datetime.now().astimezone()
    for reminder in reminders:
        run_at = reminder.next_run_at
        if run_at is None:
            continue
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=now.tzinfo)
        if run_at <= now:
            await send_reminder(bot, reminder.id)
        else:
            schedule_reminder(bot, reminder.id, run_at)

    logger.info("Restored %s scheduled reminders", len(reminders))
