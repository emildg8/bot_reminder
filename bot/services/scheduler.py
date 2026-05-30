"""Планировщик напоминаний — отправка и восстановление после рестарта."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select

from bot.db.models import Reminder, ReminderKind
from bot.db.repository import (
    async_session,
    clear_reminder_next_run,
    get_reminder,
    is_chat_paused,
    update_reminder_next_run,
)
from bot.keyboards.inline import reminder_actions_keyboard
from bot.services.reminder_utils import advance_reminder
from bot.services.telegram_format import format_reminder_message, is_group_chat

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

RESTORE_JITTER_SECONDS = 3
RESTORE_JITTER_CAP_SECONDS = 120
SEND_RETRY_MINUTES = 2
PAUSE_RETRY_MINUTES = 5


async def send_reminder(bot: Bot, reminder_id: int) -> None:
    try:
        await _send_reminder_impl(bot, reminder_id)
    except Exception as exc:
        logger.exception("Unhandled error sending reminder %s: %s", reminder_id, exc)
        retry_at = datetime.now().astimezone() + timedelta(minutes=SEND_RETRY_MINUTES)
        schedule_reminder(bot, reminder_id, retry_at)


async def _send_reminder_impl(bot: Bot, reminder_id: int) -> None:
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            return

        if await is_chat_paused(session, reminder.chat_id):
            logger.info("Chat %s paused, reschedule reminder %s", reminder.chat_id, reminder_id)
            retry_at = datetime.now().astimezone() + timedelta(minutes=PAUSE_RETRY_MINUTES)
            await update_reminder_next_run(session, reminder, retry_at)
            schedule_reminder(bot, reminder.id, retry_at)
            try:
                await bot.send_message(
                    reminder.created_by_telegram_id,
                    f"⏸ Чат на паузе — напоминание #{reminder.id} «{reminder.text}» "
                    f"перенесено на {retry_at.strftime('%H:%M')}.",
                )
            except Exception:
                pass
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

        is_once = reminder.kind == ReminderKind.ONCE.value
        job_id = f"reminder_{reminder_id}"
        planned_next: datetime | None = None

        if is_once:
            # once: сначала убираем next_run_at — после рестарта не будет повторной отправки
            await clear_reminder_next_run(session, reminder)
        else:
            # recurring: сразу фиксируем следующий запуск — падение после send не дублирует текущий
            planned_next = advance_reminder(reminder, reminder.timezone)
            if planned_next is not None:
                await update_reminder_next_run(session, reminder, planned_next)

        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

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
            logger.exception("Failed to send reminder %s: %s", reminder_id, exc)
            retry_at = datetime.now().astimezone() + timedelta(minutes=SEND_RETRY_MINUTES)
            await update_reminder_next_run(session, reminder, retry_at)
            schedule_reminder(bot, reminder.id, retry_at)
            return

        if planned_next is not None:
            schedule_reminder(bot, reminder.id, planned_next)


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
        max_instances=1,
        coalesce=True,
    )
    logger.info("Scheduled reminder %s at %s", reminder_id, run_at.isoformat())


def compute_restore_run_at(now: datetime, overdue_index: int) -> datetime:
    """Разносит просроченные напоминания при старте, чтобы не получить 429 от Telegram."""
    delay = min(overdue_index * RESTORE_JITTER_SECONDS, RESTORE_JITTER_CAP_SECONDS)
    return now + timedelta(seconds=delay)


async def restore_scheduled_reminders(bot: Bot) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Reminder).where(Reminder.is_active.is_(True), Reminder.next_run_at.is_not(None))
        )
        reminders = list(result.scalars().all())

    now = datetime.now().astimezone()
    overdue_index = 0
    future_count = 0

    for reminder in reminders:
        run_at = reminder.next_run_at
        if run_at is None:
            continue
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=now.tzinfo)

        if run_at <= now:
            restore_at = compute_restore_run_at(now, overdue_index)
            schedule_reminder(bot, reminder.id, restore_at)
            overdue_index += 1
            logger.info(
                "Overdue reminder %s (%s), restore at %s",
                reminder.id,
                reminder.kind,
                restore_at.isoformat(),
            )
        else:
            schedule_reminder(bot, reminder.id, run_at)
            future_count += 1

    logger.info(
        "Restored %s reminders (%s future, %s overdue with jitter)",
        len(reminders),
        future_count,
        overdue_index,
    )


def count_scheduled_reminder_jobs() -> int:
    return len([j for j in scheduler.get_jobs() if j.id.startswith("reminder_")])
