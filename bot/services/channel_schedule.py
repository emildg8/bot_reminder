"""Планируемые посты в канале через Telegram schedule_date."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.methods import SendMessage
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder, ReminderKind
from bot.db.repository import update_reminder_telegram_schedule
from bot.services.reminder_utils import ensure_future_run_at, local_run_at
from bot.services.telegram_format import format_reminder_message

logger = logging.getLogger(__name__)

MIN_SCHEDULE_SECONDS = 11
MAX_SCHEDULE_DAYS = 365


def _can_use_telegram_schedule(run_at_utc: datetime) -> bool:
    now = datetime.now(UTC)
    delta = (run_at_utc - now).total_seconds()
    return MIN_SCHEDULE_SECONDS <= delta <= MAX_SCHEDULE_DAYS * 86400


async def try_schedule_channel_post(
    bot: Bot,
    *,
    channel_id: int,
    text: str,
    run_at_utc: datetime,
) -> int | None:
    if not _can_use_telegram_schedule(run_at_utc):
        return None
    try:
        msg = await bot(
            SendMessage(
                chat_id=channel_id,
                text=text,
                schedule_date=int(run_at_utc.timestamp()),
            )
        )
        return msg.message_id
    except Exception as exc:
        logger.warning(
            "Telegram schedule_date failed for channel %s: %s",
            channel_id,
            exc,
        )
        return None


async def cancel_channel_scheduled_post(
    bot: Bot,
    channel_id: int,
    message_id: int,
) -> None:
    try:
        await bot.delete_message(channel_id, message_id)
    except Exception as exc:
        logger.debug(
            "Cannot delete scheduled channel message %s in %s: %s",
            message_id,
            channel_id,
            exc,
        )


async def cancel_reminder_telegram_schedule(
    bot: Bot,
    session: AsyncSession,
    reminder: Reminder,
) -> None:
    if not reminder.telegram_schedule_message_id:
        return
    await cancel_channel_scheduled_post(
        bot,
        reminder.chat_id,
        reminder.telegram_schedule_message_id,
    )
    await update_reminder_telegram_schedule(session, reminder, None)


async def setup_channel_telegram_schedule(
    bot: Bot,
    session: AsyncSession,
    reminder: Reminder,
) -> bool:
    """Разовое напоминание в канале — native scheduled post + DM через APScheduler."""
    if reminder.kind != ReminderKind.ONCE.value:
        return False

    try:
        chat = await bot.get_chat(reminder.chat_id)
    except Exception:
        return False
    if chat.type != ChatType.CHANNEL:
        return False

    run_at = local_run_at(reminder.next_run_at, reminder.timezone)
    if run_at is None:
        return False
    run_at_utc = ensure_future_run_at(run_at, reminder.timezone)

    if reminder.telegram_schedule_message_id:
        await cancel_reminder_telegram_schedule(bot, session, reminder)

    body = format_reminder_message(
        reminder.text,
        chat_id=reminder.chat_id,
        chat_type=ChatType.CHANNEL,
        chat_title=chat.title,
    )
    msg_id = await try_schedule_channel_post(
        bot,
        channel_id=reminder.chat_id,
        text=body,
        run_at_utc=run_at_utc,
    )
    if msg_id is None:
        return False

    await update_reminder_telegram_schedule(session, reminder, msg_id)
    logger.info(
        "Channel reminder %s scheduled via Telegram at %s",
        reminder.id,
        run_at_utc.isoformat(),
    )
    return True
