from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.db.models import Reminder, ReminderKind
from bot.services.nlp.schemas import ParsedReminder


def weekdays_to_mask(weekdays: list[int]) -> int:
    mask = 0
    for d in weekdays:
        if 0 <= d <= 6:
            mask |= 1 << d
    return mask


def mask_to_weekdays(mask: int) -> list[int]:
    return [d for d in range(7) if mask & (1 << d)]


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

    if parsed.kind == "weekly":
        if parsed.daily_time is None or not parsed.weekdays:
            raise ValueError("weekly reminder requires daily_time and weekdays")
        return _next_weekly_run(now, parsed.daily_time, set(parsed.weekdays))

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

    if reminder.kind == ReminderKind.WEEKLY.value and reminder.daily_time and reminder.weekdays_mask:
        weekdays = set(mask_to_weekdays(reminder.weekdays_mask))
        return _next_weekly_run(now, reminder.daily_time, weekdays)

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

    if parsed.kind == "weekly" and parsed.daily_time and parsed.weekdays:
        when = parsed.daily_time.strftime("%H:%M")
        wd = set(parsed.weekdays)
        if wd == {0, 1, 2, 3, 4}:
            days = "по будням"
        elif wd == {5, 6}:
            days = "по выходным"
        else:
            names = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
            days = " ".join(names[d] for d in sorted(wd))
        return f"{days} в {when}: {parsed.text}"

    return parsed.text


def _next_weekly_run(now: datetime, daily_time: time, allowed_weekdays: set[int]) -> datetime:
    base = now.replace(
        hour=daily_time.hour,
        minute=daily_time.minute,
        second=0,
        microsecond=0,
    )
    for offset_days in range(0, 8):
        candidate = base + timedelta(days=offset_days)
        if candidate.weekday() in allowed_weekdays and candidate > now:
            return candidate
    # fallback: next week same day
    return base + timedelta(days=7)
