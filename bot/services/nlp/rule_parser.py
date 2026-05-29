import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import dateparser

from bot.services.nlp.schemas import ParsedReminder
from bot.services.nlp.weekday_parse import find_custom_weekly

INTERVAL_PATTERN = re.compile(
    r"кажды(?:е|й)\s+(\d+)\s*(минут(?:у|ы)?|мин|час(?:а|ов)?|ч)\b",
    re.IGNORECASE,
)
DAILY_PATTERN = re.compile(
    r"каждый\s+день\s+(?:в\s+)?(\d{1,2})[:.](\d{2})",
    re.IGNORECASE,
)
WEEKDAYS_PATTERN = re.compile(
    r"(?:по\s+)?будням\s+(?:в\s+)?(\d{1,2})[:.](\d{2})",
    re.IGNORECASE,
)
WEEKEND_PATTERN = re.compile(
    r"(?:по\s+)?выходным\s+(?:в\s+)?(\d{1,2})[:.](\d{2})",
    re.IGNORECASE,
)
IN_PATTERN = re.compile(
    r"через\s+(\d+)\s*(минут(?:у|ы)?|мин|час(?:а|ов)?|ч)\b",
    re.IGNORECASE,
)
EVERY_HOUR_PATTERN = re.compile(r"каждый\s+час", re.IGNORECASE)
REMINDER_PREFIX = re.compile(
    r"^(?:напомни(?:ть)?|напоминание|remind(?:\s+me)?)\s*(?:что|о|about|to)?\s*",
    re.IGNORECASE,
)


def _strip_prefix(text: str) -> str:
    return REMINDER_PREFIX.sub("", text).strip(" ,.")


def _parse_duration(value: int, unit: str) -> int:
    unit = unit.lower()
    if unit.startswith("ч"):
        return value * 3600
    return value * 60


def parse_with_rules(text: str, timezone: str) -> ParsedReminder | None:
    raw = text.strip()
    if not raw:
        return None

    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    cleaned = _strip_prefix(raw)

    if match := EVERY_HOUR_PATTERN.search(cleaned):
        task_text = EVERY_HOUR_PATTERN.sub("", cleaned).strip(" ,.")
        if not task_text:
            task_text = cleaned
        return ParsedReminder(
            text=task_text or "Перерыв",
            kind="interval",
            interval_seconds=3600,
            run_at=now + timedelta(hours=1),
        )

    if match := IN_PATTERN.search(cleaned):
        seconds = _parse_duration(int(match.group(1)), match.group(2))
        task_text = IN_PATTERN.sub("", cleaned).strip(" ,.")
        return ParsedReminder(
            text=task_text or "Напоминание",
            kind="once",
            run_at=now + timedelta(seconds=seconds),
        )

    if match := INTERVAL_PATTERN.search(cleaned):
        seconds = _parse_duration(int(match.group(1)), match.group(2))
        task_text = INTERVAL_PATTERN.sub("", cleaned).strip(" ,.")
        if not task_text:
            task_text = cleaned
        return ParsedReminder(
            text=task_text or "Напоминание",
            kind="interval",
            interval_seconds=seconds,
            run_at=now + timedelta(seconds=seconds),
        )

    if match := DAILY_PATTERN.search(cleaned):
        hour, minute = int(match.group(1)), int(match.group(2))
        task_text = DAILY_PATTERN.sub("", cleaned).strip(" ,.")
        daily = time(hour, minute)
        next_run = _next_daily_run(now, daily)
        return ParsedReminder(
            text=task_text or "Ежедневное напоминание",
            kind="daily",
            daily_time=daily,
            run_at=next_run,
        )

    if match := WEEKDAYS_PATTERN.search(cleaned):
        hour, minute = int(match.group(1)), int(match.group(2))
        task_text = WEEKDAYS_PATTERN.sub("", cleaned).strip(" ,.")
        daily = time(hour, minute)
        return ParsedReminder(
            text=task_text or "Напоминание",
            kind="weekly",
            daily_time=daily,
            weekdays=[0, 1, 2, 3, 4],
        )

    if match := WEEKEND_PATTERN.search(cleaned):
        hour, minute = int(match.group(1)), int(match.group(2))
        task_text = WEEKEND_PATTERN.sub("", cleaned).strip(" ,.")
        daily = time(hour, minute)
        return ParsedReminder(
            text=task_text or "Напоминание",
            kind="weekly",
            daily_time=daily,
            weekdays=[5, 6],
        )

    if custom := find_custom_weekly(cleaned):
        weekdays, hour, minute, task_text = custom
        daily = time(hour, minute)
        return ParsedReminder(
            text=task_text or "Напоминание",
            kind="weekly",
            daily_time=daily,
            weekdays=weekdays,
        )

    parsed_date = dateparser.parse(
        cleaned,
        languages=["ru", "en"],
        settings={
            "TIMEZONE": timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    )
    if parsed_date is None:
        return None

    task_text = cleaned
    for pattern in (
        IN_PATTERN,
        DAILY_PATTERN,
        WEEKDAYS_PATTERN,
        WEEKEND_PATTERN,
        INTERVAL_PATTERN,
        EVERY_HOUR_PATTERN,
    ):
        task_text = pattern.sub("", task_text).strip(" ,.")

    if parsed_date <= now:
        parsed_date = parsed_date + timedelta(days=1)

    return ParsedReminder(
        text=task_text or cleaned,
        kind="once",
        run_at=parsed_date,
    )


def _next_daily_run(now: datetime, daily_time: time) -> datetime:
    candidate = now.replace(
        hour=daily_time.hour,
        minute=daily_time.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate
