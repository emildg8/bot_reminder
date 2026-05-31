"""Поиск похожих активных напоминаний."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import local_run_at, weekdays_to_mask


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def schedules_match(reminder: Reminder, parsed: ParsedReminder, timezone: str) -> bool:
    """True, если расписание совпадает — иначе тот же текст в другое время не дубликат."""
    if reminder.kind != parsed.kind:
        return False

    if parsed.kind == "once":
        if parsed.delay_seconds:
            return False
        if parsed.run_at is None or reminder.next_run_at is None:
            return False
        tz = ZoneInfo(timezone)
        r_at = local_run_at(reminder.next_run_at, reminder.timezone)
        if r_at is None:
            return False
        p_at = parsed.run_at
        if p_at.tzinfo is None:
            p_at = p_at.replace(tzinfo=tz)
        r_local = r_at.astimezone(tz).replace(second=0, microsecond=0)
        p_local = p_at.astimezone(tz).replace(second=0, microsecond=0)
        return r_local == p_local

    if parsed.kind == "daily":
        return reminder.daily_time == parsed.daily_time

    if parsed.kind == "weekly":
        r_mask = reminder.weekdays_mask or 0
        p_mask = weekdays_to_mask(parsed.weekdays) if parsed.weekdays else 0
        return r_mask == p_mask and reminder.daily_time == parsed.daily_time

    if parsed.kind == "interval":
        return reminder.interval_seconds == parsed.interval_seconds

    return False


async def find_duplicate_reminder(
    session: AsyncSession,
    chat_id: int,
    text: str,
    kind: str,
    *,
    parsed: ParsedReminder | None = None,
    timezone: str = "Europe/Moscow",
    created_by: int | None = None,
) -> Reminder | None:
    normalized = normalize_text(text)
    query = select(Reminder).where(
        Reminder.chat_id == chat_id,
        Reminder.is_active.is_(True),
        Reminder.kind == kind,
    )
    if created_by is not None:
        query = query.where(Reminder.created_by_telegram_id == created_by)

    result = await session.execute(query)
    for reminder in result.scalars().all():
        if normalize_text(reminder.text) != normalized:
            continue
        if parsed is not None and not schedules_match(reminder, parsed, timezone):
            continue
        return reminder
    return None
