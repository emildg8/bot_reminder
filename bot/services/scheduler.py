import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select

from bot.db.models import Reminder
from bot.db.repository import async_session, get_reminder, update_reminder_next_run
from bot.keyboards.inline import reminder_actions_keyboard
from bot.services.reminder_utils import advance_reminder
from bot.services.telegram_format import format_reminder_message, is_group_chat

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def send_reminder(bot: Bot, reminder_id: int) -> None:
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            return

        mention_username: str | None = None
        creator_username: str | None = None
        if reminder.mention_telegram_id:
            try:
                chat = await bot.get_chat(reminder.mention_telegram_id)
                mention_username = chat.username
            except Exception:
                pass
        try:
            creator_chat = await bot.get_chat(reminder.created_by_telegram_id)
            creator_username = creator_chat.username
        except Exception:
            pass

        body = format_reminder_message(
            reminder.text,
            mention_user_id=reminder.mention_telegram_id,
            mention_username=mention_username,
            creator_user_id=reminder.created_by_telegram_id,
            creator_username=creator_username,
            chat_id=reminder.chat_id,
        )

        in_group = is_group_chat(reminder.chat_id)
        group_hint = ""
        if in_group:
            group_hint = "\n\n<i>Управление — в личке с ботом.</i>"

        try:
            await bot.send_message(
                chat_id=reminder.chat_id,
                text=body + group_hint,
                reply_markup=None if in_group else reminder_actions_keyboard(reminder.id),
            )
            if in_group:
                try:
                    await bot.send_message(
                        reminder.created_by_telegram_id,
                        f"⏰ Напоминание в группе (#{reminder.id}):\n{body}",
                        reply_markup=reminder_actions_keyboard(reminder.id),
                    )
                except Exception as dm_exc:
                    logger.warning(
                        "Cannot DM creator %s for reminder %s: %s",
                        reminder.created_by_telegram_id,
                        reminder_id,
                        dm_exc,
                    )
        except Exception as exc:
            # Network / Telegram errors: retry позже, не двигая расписание навсегда.
            logger.exception("Failed to send reminder %s: %s", reminder_id, exc)
            retry_at = datetime.now().astimezone() + timedelta(minutes=2)
            schedule_reminder(bot, reminder.id, retry_at)
            return

        next_run = advance_reminder(reminder, reminder.timezone)
        job_id = f"reminder_{reminder_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        if next_run is None:
            # once: остаётся активным до «Готово»/«Удалить», чтобы работал snooze
            pass
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
