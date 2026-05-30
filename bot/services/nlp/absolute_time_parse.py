"""Парсинг «завтра в 14:00», «сегодня в 9.00» и похожих фраз."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.services.nlp.schemas import ParsedReminder

# 14.00 → 14:00
TIME_DOT_PATTERN = re.compile(r"\b(\d{1,2})\.(\d{2})\b")

# завтра в 14:00 / завтра 14:00
DAY_AT_TIME = re.compile(
    r"(?P<day>сегодня|завтра|послезавтра|после\s+завтра)"
    r"\s+(?:в\s+)?(?P<h>\d{1,2})[:.](?P<m>\d{2})\b",
    re.IGNORECASE,
)

# в 14:00 завтра
TIME_THEN_DAY = re.compile(
    r"\b(?:в\s+)?(?P<h>\d{1,2})[:.](?P<m>\d{2})\s+(?P<day>сегодня|завтра|послезавтра|после\s+завтра)\b",
    re.IGNORECASE,
)

# завтра созвон / созвон завтра (без времени → 9:00)
DAY_ONLY_PREFIX = re.compile(
    r"^(?P<day>сегодня|завтра|послезавтра|после\s+завтра)\s+(?P<task>.+)$",
    re.IGNORECASE,
)
DAY_ONLY_SUFFIX = re.compile(
    r"^(?P<task>.+?)\s+(?P<day>сегодня|завтра|послезавтра|после\s+завтра)$",
    re.IGNORECASE,
)

DEFAULT_DAY_HOUR = 9
DEFAULT_DAY_MINUTE = 0
AT_TIME_ONLY = re.compile(
    r"\b(?:в\s+)(?P<h>\d{1,2})[:.](?P<m>\d{2})\b",
    re.IGNORECASE,
)

DAY_OFFSETS = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
    "после завтра": 2,
}

_REMINDER_VERB = r"(?:напомни(?:ть|м)?|напомню|напомним|напоминание|remind(?:\s+me)?)"

NOISE_PREFIX = re.compile(
    rf"^(?:бот|bot|{_REMINDER_VERB})\s*[,]?\s*",
    re.IGNORECASE,
)

# «завтра в 2» / «в 14» без минут → «в 2:00» / «в 14:00»
BARE_HOUR = re.compile(r"(\b(?:в\s+))(\d{1,2})(?![:.]\d)(\b)", re.IGNORECASE)

DAY_ONLY_WORD = re.compile(
    r"^(?:сегодня|завтра|послезавтра|после\s+завтра)$",
    re.IGNORECASE,
)


def normalize_time_dots(text: str) -> str:
    return TIME_DOT_PATTERN.sub(r"\1:\2", text)


def normalize_bare_hours(text: str) -> str:
    return BARE_HOUR.sub(r"\1\2:00\3", text)


def normalize_phrase(text: str) -> str:
    return normalize_bare_hours(normalize_time_dots(text.strip()))


def _day_offset(day_token: str) -> int:
    key = day_token.lower().replace("  ", " ").strip()
    return DAY_OFFSETS.get(key, 0)


def _build_run_at(now: datetime, day_offset: int, hour: int, minute: int) -> datetime:
    base = (now + timedelta(days=day_offset)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if day_offset == 0 and base <= now:
        base += timedelta(days=1)
    return base


def _extract_task(full: str, match: re.Match) -> str:
    task = (full[: match.start()] + full[match.end() :]).strip(" ,.—–-")
    task = NOISE_PREFIX.sub("", task).strip()
    task = re.sub(r"\s+", " ", task)
    return task or "Напоминание"


def parse_absolute_datetime(text: str, timezone: str) -> ParsedReminder | None:
    normalized = normalize_phrase(text)
    if not normalized:
        return None

    tz = ZoneInfo(timezone)
    now = datetime.now(tz)

    for pattern in (DAY_AT_TIME, TIME_THEN_DAY):
        if match := pattern.search(normalized):
            day = match.group("day")
            hour, minute = int(match.group("h")), int(match.group("m"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                continue
            run_at = _build_run_at(now, _day_offset(day), hour, minute)
            task = _extract_task(normalized, match)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    for pattern in (DAY_ONLY_PREFIX, DAY_ONLY_SUFFIX):
        if match := pattern.match(normalized):
            day = match.group("day")
            task = NOISE_PREFIX.sub("", match.group("task")).strip()
            task = re.sub(r"\s+", " ", task) or "Напоминание"
            run_at = _build_run_at(now, _day_offset(day), DEFAULT_DAY_HOUR, DEFAULT_DAY_MINUTE)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    if match := AT_TIME_ONLY.search(normalized):
        hour, minute = int(match.group("h")), int(match.group("m"))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            run_at = _build_run_at(now, 0, hour, minute)
            task = _extract_task(normalized, match)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    return None


def try_dateparser_search(text: str, timezone: str) -> ParsedReminder | None:
    """dateparser.search — вытаскивает дату из середины фразы."""
    try:
        from dateparser.search import search_dates
    except ImportError:
        return None

    normalized = normalize_phrase(text)
    settings = {
        "TIMEZONE": timezone,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    found = search_dates(normalized, languages=["ru", "en"], settings=settings)
    if not found:
        return None

    # Берём фрагмент с наиболее конкретным временем (не только дата)
    phrase, run_at = found[-1]
    if DAY_ONLY_WORD.match(phrase.strip()) and BARE_HOUR.search(normalized):
        return None
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=ZoneInfo(timezone))
    else:
        run_at = run_at.astimezone(ZoneInfo(timezone))

    now = datetime.now(ZoneInfo(timezone))
    if run_at <= now:
        run_at += timedelta(days=1)

    task = normalized.replace(phrase, "").strip(" ,.—–-")
    task = NOISE_PREFIX.sub("", task).strip()
    task = re.sub(r"\s+", " ", task)
    if not task:
        task = "Напоминание"

    return ParsedReminder(text=task, kind="once", run_at=run_at)
