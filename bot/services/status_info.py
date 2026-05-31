"""Ближайшее напоминание для /status."""

from __future__ import annotations

from datetime import datetime

from bot.db.models import Reminder
from bot.services.reminder_utils import local_run_at
from bot.services.timezone_labels import format_timezone_label


def format_next_reminder_line(reminders: list[Reminder], timezone: str) -> str | None:
    upcoming: list[tuple[datetime, Reminder]] = []
    for reminder in reminders:
        run_at = local_run_at(reminder.next_run_at, reminder.timezone or timezone)
        if run_at is not None:
            upcoming.append((run_at, reminder))

    if not upcoming:
        return None

    run_at, reminder = min(upcoming, key=lambda item: item[0])
    tz_label = format_timezone_label(reminder.timezone or timezone)
    when = run_at.strftime("%d.%m %H:%M")
    text = reminder.text if len(reminder.text) <= 40 else reminder.text[:37] + "…"
    return f"⏭ Ближайшее: <b>{when}</b> ({tz_label}) · #{reminder.id} · {text}"
