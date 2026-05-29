from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.db.models import Reminder, ReminderKind
from bot.services.nlp.schemas import ParsedReminder


def compute_next_run(parsed: ParsedReminder, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)

    if parsed.kind == "once":
        if parsed.run_at is None:
            raise ValueError("once reminder requires run_at")
        run_at = parsed.run_at
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=tz)
        return run_at.astimezone(tz)

    if parsed.kind == "interval":
        if parsed.run_at is not None:
            run_at = parsed.run_at
            if run_at.tzinfo is None:
                run_at = run_at.replace(tzinfo=tz)
            return run_at.astimezone(tz)
        seconds = parsed.interval_seconds or 3600
        return now + timedelta(seconds=seconds)

    if parsed.kind == "daily":
        if parsed.daily_time is None:
            raise ValueError("daily reminder requires daily_time")
        candidate = now.replace(
            hour=parsed.daily_time.hour,
            minute=parsed.daily_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    raise ValueError(f"Unknown kind: {parsed.kind}")


def advance_reminder(reminder: Reminder, timezone: str) -> datetime | None:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)

    if reminder.kind == ReminderKind.ONCE.value:
        return None

    if reminder.kind == ReminderKind.INTERVAL.value:
        seconds = reminder.interval_seconds or 3600
        base = reminder.next_run_at or now
        if base.tzinfo is None:
            base = base.replace(tzinfo=tz)
        return base.astimezone(tz) + timedelta(seconds=seconds)

    if reminder.kind == ReminderKind.DAILY.value and reminder.daily_time:
        candidate = now.replace(
            hour=reminder.daily_time.hour,
            minute=reminder.daily_time.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    return None


def format_reminder_summary(parsed: ParsedReminder, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    next_run = compute_next_run(parsed, timezone).astimezone(tz)

    if parsed.kind == "once":
        when = next_run.strftime("%d.%m.%Y %H:%M")
        return f"Напомню {when}: {parsed.text}"

    if parsed.kind == "interval":
        seconds = parsed.interval_seconds or 3600
        if seconds % 3600 == 0:
            interval = f"каждые {seconds // 3600} ч."
        else:
            interval = f"каждые {seconds // 60} мин."
        when = next_run.strftime("%H:%M")
        return f"{interval}, первый раз в {when}: {parsed.text}"

    if parsed.kind == "daily" and parsed.daily_time:
        when = parsed.daily_time.strftime("%H:%M")
        return f"Каждый день в {when}: {parsed.text}"

    return parsed.text
