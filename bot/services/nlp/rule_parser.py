import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from bot.services.nlp.absolute_time_parse import (
    HOUR_WORD_PATTERN,
    normalize_phrase,
    parse_absolute_datetime,
    parse_number_token,
    try_dateparser_search,
)
from bot.services.nlp.schemas import ParsedReminder
from bot.services.nlp.weekday_parse import find_custom_weekly, find_weekly_schedules

INTERVAL_HALF_HOUR = re.compile(r"кажды(?:е|й)\s+полчаса\b", re.IGNORECASE)
INTERVAL_PATTERN = re.compile(
    r"кажды(?:е|й)\s+(\d+)\s*(минут(?:у|ы)?|мин|час(?:а|ов)?|ч)\b",
    re.IGNORECASE,
)
INTERVAL_WORD_PATTERN = re.compile(
    rf"кажды(?:е|й)\s+(?P<n>{HOUR_WORD_PATTERN}|\d+)\s*(?:минут(?:у|ы)?|мин|час(?:а|ов)?|ч)\b",
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
IN_RANGE_PATTERN = re.compile(
    r"через\s+(\d+)\s*[-–—]\s*(\d+)\s*(минут(?:у|ы)?|мин|час(?:а|ов)?|ч|день|дня|дней)\b",
    re.IGNORECASE,
)
IN_WORD_RANGE = re.compile(
    rf"через\s+(?P<a>{HOUR_WORD_PATTERN}|\d+)\s*[-–—]\s*"
    rf"(?P<b>{HOUR_WORD_PATTERN}|\d+)\s*(?:час(?:а|ов)?)\b",
    re.IGNORECASE,
)
IN_COUPLE_PATTERN = re.compile(
    r"через\s+пару\s+(минут(?:у|ы)?|мин|час(?:а|ов)?|ч)\b",
    re.IGNORECASE,
)
IN_FEW_HOURS = re.compile(r"через\s+(?:несколько|неск\.?)\s+час(?:а|ов)?\b", re.IGNORECASE)
IN_HALF_HOUR = re.compile(r"через\s+полчаса\b", re.IGNORECASE)
IN_HOUR_WORD = re.compile(r"через\s+(?:один\s+|1\s+)?час\b", re.IGNORECASE)
IN_ONE_AND_HALF_HOUR = re.compile(r"через\s+полтора\s+часа\b", re.IGNORECASE)
IN_WORD_HOURS = re.compile(
    rf"через\s+(?P<n>{HOUR_WORD_PATTERN}|\d+)\s*(?:час(?:а|ов)?)\b",
    re.IGNORECASE,
)
IN_WORD_MINUTES = re.compile(
    rf"через\s+(?P<n>{HOUR_WORD_PATTERN}|\d+)\s*(?:минут(?:у|ы)?|мин)\b",
    re.IGNORECASE,
)
IN_WEEK = re.compile(
    r"через\s+(?:(\d+)\s+)?(?:недел(?:ю|и|ь)|нед)\b",
    re.IGNORECASE,
)
DAILY_ALT_PATTERN = re.compile(
    r"ежедневно\s+(?:в\s+)?(\d{1,2})[:.](\d{2})",
    re.IGNORECASE,
)
EVERY_HOUR_PATTERN = re.compile(r"каждый\s+час", re.IGNORECASE)
_REMINDER_VERB = (
    r"(?:напомни(?:ть|м)?(?:\s+мне)?|напомню(?:\s+мне)?|"
    r"напомним|напоминание|remind(?:\s+me)?)"
)
REMINDER_PREFIX = re.compile(
    rf"^{_REMINDER_VERB}\s*(?:[,]|\s*(?:что|о|about|to))?\s*",
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


def _parse_count_token(token: str) -> int | None:
    return parse_number_token(token)


def _task_without_pattern(cleaned: str, pattern: re.Pattern) -> str:
    return pattern.sub("", cleaned).strip(" ,.") or "Напоминание"


def parse_with_rules(text: str, timezone: str) -> ParsedReminder | None:
    raw = text.strip()
    if not raw:
        return None

    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    cleaned = normalize_phrase(_strip_prefix(raw))

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

    if match := IN_COUPLE_PATTERN.search(cleaned):
        unit = match.group(1).lower()
        seconds = 7200 if unit.startswith("ч") else 120
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_COUPLE_PATTERN),
            kind="once",
            run_at=now + timedelta(seconds=seconds),
        )

    if match := IN_FEW_HOURS.search(cleaned):
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_FEW_HOURS),
            kind="once",
            run_at=now + timedelta(hours=3),
        )

    if match := IN_RANGE_PATTERN.search(cleaned):
        low, high = int(match.group(1)), int(match.group(2))
        value = max(low, high)
        seconds = _parse_duration(value, match.group(3))
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_RANGE_PATTERN),
            kind="once",
            run_at=now + timedelta(seconds=seconds),
        )

    if match := IN_WORD_RANGE.search(cleaned):
        a = _parse_count_token(match.group("a"))
        b = _parse_count_token(match.group("b"))
        if a and b:
            hours = max(a, b)
            return ParsedReminder(
                text=_task_without_pattern(cleaned, IN_WORD_RANGE),
                kind="once",
                run_at=now + timedelta(hours=hours),
            )

    if match := IN_ONE_AND_HALF_HOUR.search(cleaned):
        return ParsedReminder(
            text=_task_without_pattern(cleaned, IN_ONE_AND_HALF_HOUR),
            kind="once",
            run_at=now + timedelta(minutes=90),
        )

    if match := IN_WORD_HOURS.search(cleaned):
        hours = _parse_count_token(match.group("n"))
        if hours and hours > 0:
            return ParsedReminder(
                text=_task_without_pattern(cleaned, IN_WORD_HOURS),
                kind="once",
                run_at=now + timedelta(hours=hours),
            )

    if match := IN_WORD_MINUTES.search(cleaned):
        minutes = _parse_count_token(match.group("n"))
        if minutes and minutes > 0:
            return ParsedReminder(
                text=_task_without_pattern(cleaned, IN_WORD_MINUTES),
                kind="once",
                run_at=now + timedelta(minutes=minutes),
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

    if match := INTERVAL_WORD_PATTERN.search(cleaned):
        count = _parse_count_token(match.group("n"))
        unit = match.group(0).lower()
        if count and count > 0:
            if "мин" in unit or "минут" in unit:
                seconds = count * 60
            else:
                seconds = count * 3600
            task_text = INTERVAL_WORD_PATTERN.sub("", cleaned).strip(" ,.")
            if not task_text:
                task_text = cleaned
            return ParsedReminder(
                text=task_text or "Напоминание",
                kind="interval",
                interval_seconds=seconds,
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

    task = cleaned
    try:
        from dateparser.search import search_dates

        found = search_dates(
            cleaned,
            languages=["ru", "en"],
            settings={
                "TIMEZONE": timezone,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
            },
        )
        if found:
            phrase, _ = found[-1]
            task = cleaned.replace(phrase, "").strip(" ,.—–-")
            task = REMINDER_PREFIX.sub("", task).strip()
    except ImportError:
        pass

    task = re.sub(r"\s+", " ", task).strip() or "Напоминание"

    return ParsedReminder(
        text=task,
        kind="once",
        run_at=parsed_date,
    )


def parse_all_with_rules(text: str, timezone: str) -> list[ParsedReminder]:
    """Все напоминания из одной фразы (несколько времён в неделю и т.п.)."""
    raw = text.strip()
    if not raw:
        return []

    cleaned = normalize_phrase(_strip_prefix(raw))
    schedules = find_weekly_schedules(cleaned)
    if schedules:
        return [
            ParsedReminder(
                text=task or "Напоминание",
                kind="weekly",
                daily_time=time(hour, minute),
                weekdays=weekdays,
            )
            for weekdays, hour, minute, task in schedules
        ]

    single = parse_with_rules(text, timezone)
    return [single] if single else []


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
