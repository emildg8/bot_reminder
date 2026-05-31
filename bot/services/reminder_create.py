"""Создание напоминаний из распарсенных items — общая логика confirm/create/edit."""

from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import ReminderEventKind
from bot.db.repository import create_reminder
from bot.services.channel_schedule import setup_channel_telegram_schedule
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_display import format_parsed_when_label
from bot.services.reminder_history import log_reminder_event
from bot.services.reminder_utils import compute_next_run, weekdays_to_mask
from bot.services.scheduler import schedule_reminder

CreatedItem = tuple[int, str, str]


async def create_and_schedule_items(
    session: AsyncSession,
    bot: Bot,
    *,
    user_id: int,
    chat_id: int,
    created_by_telegram_id: int,
    timezone: str,
    parsed_items: list[ParsedReminder],
    mention_telegram_id: int | None = None,
) -> list[CreatedItem]:
    created: list[CreatedItem] = []
    for parsed in parsed_items:
        next_run = compute_next_run(parsed, timezone)
        reminder = await create_reminder(
            session,
            user_id=user_id,
            chat_id=chat_id,
            created_by_telegram_id=created_by_telegram_id,
            timezone=timezone,
            text=parsed.text,
            kind=parsed.kind,
            next_run_at=next_run,
            interval_seconds=parsed.interval_seconds,
            daily_time=parsed.daily_time,
            weekdays_mask=weekdays_to_mask(parsed.weekdays) if parsed.weekdays else None,
            mention_telegram_id=mention_telegram_id,
        )
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=chat_id,
            user_telegram_id=created_by_telegram_id,
            text=parsed.text,
            kind=ReminderEventKind.CREATED,
        )
        schedule_reminder(bot, reminder.id, next_run, timezone=timezone)
        await setup_channel_telegram_schedule(bot, session, reminder)
        when = format_parsed_when_label(parsed, timezone)
        created.append((reminder.id, when, parsed.text))
    return created
