import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.services.nlp.absolute_time_parse import (
    normalize_time_dots,
    parse_absolute_datetime,
    try_dateparser_search,
)
from bot.services.nlp.schemas import ParsedReminder
from bot.services.nlp.weekday_parse import find_custom_weekly

INTERVAL_HALF_HOUR = re.compile(r"кажды(?:е|й)\s+полчаса\b", re.IGNORECASE)
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
    r"через\s+(\d+)\s*(минут(?:у|ы)?|мин|час(?:а|ов)?|ч|день|дня|дней)\b",
    re.IGNORECASE,
)
IN_HALF_HOUR = re.compile(r"через\s+полчаса\b", re.IGNORECASE)
IN_HOUR_WORD = re.compile(r"через\s+(?:один\s+|1\s+)?час\b", re.IGNORECASE)
IN_ONE_AND_HALF_HOUR = re.compile(r"через\s+полтора\s+часа\b", re.IGNORECASE)
IN_WEEK = re.compile(
    r"через\s+(?:(\d+)\s+)?(?:недел(?:ю|и|ь)|нед)\b",
    re.IGNORECASE,
)
DAILY_ALT_PATTERN = re.compile(
    r"ежедневно\s+(?:в\s+)?(\d{1,2})[:.](\d{2})",
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
    if unit.startswith("д"):
        return value * 86400
    return value * 60


def _task_without_pattern(cleaned: str, pattern: re.Pattern) -> str:
    return pattern.sub("", cleaned).strip(" ,.") or "Напоминание"


def parse_with_rules(text: str, timezone: str) -> ParsedReminder | None:
    raw = text.strip()
    if not raw:
        return None

    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    cleaned = normalize_time_dots(_strip_prefix(raw))

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

    if match := INTERVAL_HALF_HOUR.search(cleaned):
        task_text = _task_without_pattern(cleaned, INTERVAL_HALF_HOUR)
        return ParsedReminder(
            text=task_text,
            kind="interval",
            interval_seconds=1800,
            run_at=now + timedelta(minutes=30),
        )

    if match := IN_HALF_HOUR.search(cleaned):
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_HALF_HOUR),
            kind="once",
            run_at=now + timedelta(minutes=30),
        )

    if match := IN_ONE_AND_HALF_HOUR.search(cleaned):
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_ONE_AND_HALF_HOUR),
            kind="once",
            run_at=now + timedelta(minutes=90),
        )

    if match := IN_HOUR_WORD.search(cleaned):
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_HOUR_WORD),
            kind="once",
            run_at=now + timedelta(hours=1),
        )

    if match := IN_WEEK.search(cleaned):
        weeks = int(match.group(1)) if match.group(1) else 1
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_WEEK),
            kind="once",
            run_at=now + timedelta(weeks=weeks),
        )

    if match := IN_PATTERN.search(cleaned):
        seconds = _parse_duration(int(match.group(1)), match.group(2))
        task_text = _task_without_pattern(cleaned, IN_PATTERN)
        return ParsedReminder(
            text=task_text,
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

    if match := DAILY_ALT_PATTERN.search(cleaned):
        hour, minute = int(match.group(1)), int(match.group(2))
        task_text = DAILY_ALT_PATTERN.sub("", cleaned).strip(" ,.")
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

    # «завтра в 14:00», «сегодня в 9.00» — до dateparser
    if absolute := parse_absolute_datetime(cleaned, timezone):
        return absolute

    if searched := try_dateparser_search(cleaned, timezone):
        return searched

    try:
        import dateparser
    except ImportError:
        return None

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

    if parsed_date <= now:
        parsed_date = parsed_date + timedelta(days=1)

    return ParsedReminder(
        text=cleaned.strip() or "Напоминание",
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
