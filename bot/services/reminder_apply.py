from datetime import datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import compute_next_run, weekdays_to_mask


async def apply_parsed_to_reminder(
    session: AsyncSession,
    reminder: Reminder,
    parsed: ParsedReminder,
    timezone: str,
) -> datetime:
    next_run = compute_next_run(parsed, timezone)
    reminder.text = parsed.text
    reminder.kind = parsed.kind
    reminder.timezone = timezone
    reminder.next_run_at = next_run
    reminder.interval_seconds = parsed.interval_seconds
    reminder.daily_time = parsed.daily_time
    reminder.weekdays_mask = weekdays_to_mask(parsed.weekdays) if parsed.weekdays else None
    reminder.is_active = True
    await session.commit()
    await session.refresh(reminder)
    return next_run
