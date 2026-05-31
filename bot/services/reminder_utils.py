from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.db.models import Reminder, ReminderKind
from bot.services.nlp.schemas import ParsedReminder

UTC = ZoneInfo("UTC")


def weekdays_to_mask(weekdays: list[int]) -> int:
    mask = 0
    for d in weekdays:
        if 0 <= d <= 6:
            mask |= 1 << d
    return mask


def mask_to_weekdays(mask: int) -> list[int]:
    return [d for d in range(7) if mask & (1 << d)]


def local_run_at(dt: datetime | None, timezone_name: str) -> datetime | None:
    """Naive значения из SQLite — в часовом поясе напоминания, не сервера."""
    if dt is None:
        return None
    tz = ZoneInfo(timezone_name)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def to_utc_storage(dt: datetime | None, timezone_name: str) -> datetime | None:
    if dt is None:
        return None
    return local_run_at(dt, timezone_name).astimezone(UTC)


def storage_next_run_at(dt: datetime | None, timezone_name: str) -> datetime | None:
    """Naive local wall clock для SQLite (см. test_run_at_timezone)."""
    if dt is None:
        return None
    local = local_run_at(dt, timezone_name)
    assert local is not None
    return local.replace(tzinfo=None)


def ensure_future_run_at(
    run_at: datetime,
    timezone_name: str,
    *,
    min_seconds: int = 3,
) -> datetime:
    """UTC-момент для APScheduler; не раньше чем через min_seconds."""
    local = local_run_at(run_at, timezone_name)
    assert local is not None
    now = datetime.now(UTC)
    target = local.astimezone(UTC)
    if target <= now:
        return now + timedelta(seconds=min_seconds)
    return target


def compute_next_run(parsed: ParsedReminder, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)

    if parsed.kind == "once":
        if parsed.delay_seconds is not None and parsed.delay_seconds > 0:
            return now + timedelta(seconds=parsed.delay_seconds)
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
        base = local_run_at(reminder.next_run_at, timezone) or now
        return base + timedelta(seconds=seconds)

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


def resolve_next_run_on_resume(reminder: Reminder, now: datetime) -> datetime | None:
    """Пересчитать next_run после снятия паузы, если время уже прошло."""
    next_run = reminder.next_run_at
    if next_run is None:
        return None

    next_run = local_run_at(next_run, reminder.timezone)
    assert next_run is not None
    now = now.astimezone(ZoneInfo(reminder.timezone)) if now.tzinfo else now.replace(tzinfo=ZoneInfo(reminder.timezone))

    if next_run > now:
        return next_run

    advanced = advance_reminder(reminder, reminder.timezone)
    if advanced is not None:
        return advanced

    if reminder.kind == ReminderKind.ONCE.value:
        return now + timedelta(minutes=1)

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
