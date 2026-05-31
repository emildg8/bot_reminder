"""Парсинг «завтра в 14:00», «сегодня в 9.00» и похожих фраз."""

from __future__ import annotations

import calendar
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

ORDINAL_GENITIVE: dict[str, int] = {
    "первого": 1,
    "первому": 1,
    "второго": 2,
    "второму": 2,
    "третьего": 3,
    "третьему": 3,
    "четвертого": 4,
    "четвертому": 4,
    "пятого": 5,
    "пятому": 5,
    "шестого": 6,
    "шестому": 6,
    "седьмого": 7,
    "седьмому": 7,
    "восьмого": 8,
    "восьмому": 8,
    "девятого": 9,
    "девятому": 9,
    "десятого": 10,
    "десятому": 10,
    "одиннадцатого": 11,
    "одиннадцатому": 11,
    "двенадцатого": 12,
    "двенадцатому": 12,
}

_ORDINAL_WORD = "|".join(sorted(ORDINAL_GENITIVE.keys(), key=len, reverse=True))

HALF_HOUR_ORDINAL = re.compile(
    rf"(?:\bв\s+)?(?:половин(?:е|а|у)\s+)(?P<ord>{_ORDINAL_WORD})(?:\s+(?:дня|днем|днём))?\b",
    re.IGNORECASE,
)

DAY_OFFSETS: dict[str, int] = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
    "после завтра": 2,
}

MONTH_GENITIVE: dict[str, int] = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

_month_words = "|".join(sorted(MONTH_GENITIVE.keys(), key=len, reverse=True))
NAMED_DATE_AT_TIME = re.compile(
    rf"(?P<d>\d{{1,2}})\s+(?P<month>{_month_words})\s+(?:в\s+)?(?P<h>\d{{1,2}})[:.](?P<m>\d{{2}})\b",
    re.IGNORECASE,
)
NAMED_DATE = re.compile(
    rf"(?P<d>\d{{1,2}})\s+(?P<month>{_month_words})\b",
    re.IGNORECASE,
)

HOUR_WORDS: dict[str, int] = {
    "один": 1,
    "одна": 1,
    "одну": 1,
    "два": 2,
    "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
    "двадцать": 20,
}

PART_DEFAULT_HOUR = {
    "утра": 9,
    "утром": 9,
    "дня": 14,
    "днем": 14,
    "вечера": 20,
    "вечером": 20,
    "ночи": 22,
    "ночью": 22,
}

PART_OF_DAY_ALIASES = {
    "днем": "дня",
    "днём": "дня",
    "утром": "утра",
    "вечером": "вечера",
    "ночью": "ночи",
}

HOUR_WORD_PATTERN = "|".join(sorted(HOUR_WORDS.keys(), key=len, reverse=True))
HOUR_TOKEN_NC = rf"(?:\d{{1,2}}|{HOUR_WORD_PATTERN})"
HOUR_TOKEN = rf"(?P<h>{HOUR_TOKEN_NC})"
PART_OF_DAY = r"дня|днем|днём|утра|утром|вечера|вечером|ночи|ночью"

TIME_IN_TASK = re.compile(
    rf"\b(?:\d{{1,2}}[:.]\d{{2}}|"
    rf"{HOUR_TOKEN_NC}\s*(?:час(?:а|ов)?\s+)?(?:{PART_OF_DAY})|"
    rf"полдень|полночь)\b",
    re.IGNORECASE,
)

_REMINDER_VERB = (
    r"(?:напомни(?:ть|м)?(?:\s+мне)?|напомню(?:\s+мне)?|"
    r"напомним|напоминание|remind(?:\s+me)?)"
)

NOISE_PREFIX = re.compile(
    rf"^(?:бот|bot|{_REMINDER_VERB})\s*[,]?\s*",
    re.IGNORECASE,
)

# «в 2 часа дня» / «два часа дня» / «в 8 вечера» (STT часто пишет словами)
HOUR_PART_OF_DAY = re.compile(
    rf"\b(?:в\s+)?{HOUR_TOKEN}\s*(?:час(?:а|ов)?\s+)?(?P<part>{PART_OF_DAY})\b",
    re.IGNORECASE,
)

# «в два» / «в 14» без минут → «в 14:00»
BARE_HOUR = re.compile(
    rf"(\b(?:в\s+))({HOUR_WORD_PATTERN}|\d{{1,2}})(?![:.]\d)(\b)",
    re.IGNORECASE,
)

DAY_ONLY_WORD = re.compile(
    r"^(?:сегодня|завтра|послезавтра|после\s+завтра)$",
    re.IGNORECASE,
)

# «завтра утром» / «завтра днём» без часа
DAY_PART_PERIOD = re.compile(
    rf"(?P<day>сегодня|завтра|послезавтра|после\s+завтра)"
    rf"\s+(?:в\s+)?(?P<part>{PART_OF_DAY})\b",
    re.IGNORECASE,
)


def normalize_time_dots(text: str) -> str:
    return TIME_DOT_PATTERN.sub(r"\1:\2", text)


def normalize_spaced_time(text: str) -> str:
    text = re.sub(r"\b(\d{1,2})\s+(\d{2})\b", r"\1:\2", text)
    text = re.sub(r"\b(\d{1,2})[-–—](\d{2})\b", r"\1:\2", text)
    return text


def normalize_spoken_zero_time(text: str) -> str:
    def repl(match: re.Match) -> str:
        hour_value = _parse_hour_token(match.group(1))
        if hour_value is None:
            return match.group(0)
        return f"{hour_value:02d}:00"

    return re.sub(
        rf"\b({HOUR_WORD_PATTERN}|\d{{1,2}})\s+ноль\s+ноль\b",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def normalize_half_ordinal(text: str) -> str:
    """«в половине четвертого» → «в 03:30», с «дня» → «в 15:30»."""

    def repl(match: re.Match) -> str:
        ord_word = match.group("ord").lower()
        ordinal = ORDINAL_GENITIVE.get(ord_word)
        if ordinal is None:
            return match.group(0)
        hour = ordinal - 1
        if re.search(r"(?:дня|днем|днём)", match.group(0), re.IGNORECASE) and 1 <= ordinal <= 11:
            hour += 12
        return f"в {hour:02d}:30"

    return HALF_HOUR_ORDINAL.sub(repl, text)


def normalize_k_time(text: str) -> str:
    """«к обеду», «к вечеру» — разговорные формулировки STT."""
    replacements = (
        (r"\bко\s+обед\b", "в 13:00"),
        (r"\bк\s+обеду\b", "в 13:00"),
        (r"\bк\s+обед\b", "в 13:00"),
        (r"\bк\s+вечеру\b", "в 20:00"),
        (r"\bк\s+утру\b", "в 09:00"),
        (r"\bк\s+полудню\b", "в 12:00"),
        (r"\bк\s+ночи\b", "в 22:00"),
    )
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def _parse_hour_token(token: str) -> int | None:
    token = token.lower().strip()
    if token.isdigit():
        hour = int(token)
        return hour if 0 <= hour <= 23 else None
    return HOUR_WORDS.get(token)


def _normalize_part_token(part: str) -> str:
    key = part.lower()
    return PART_OF_DAY_ALIASES.get(key, key)


def _hour_from_part_of_day(hour: int, part: str) -> int:
    part = _normalize_part_token(part)
    if part in ("дня", "вечера"):
        if 1 <= hour <= 11:
            return hour + 12
        return hour
    if part == "утра":
        return 0 if hour == 12 else hour
    if part == "ночи":
        return 0 if hour == 12 else hour
    return hour


def normalize_part_of_day(text: str) -> str:
    def repl(match: re.Match) -> str:
        hour_value = _parse_hour_token(match.group("h"))
        if hour_value is None:
            return match.group(0)
        hour = _hour_from_part_of_day(hour_value, match.group("part"))
        return f"в {hour:02d}:00"

    text = HOUR_PART_OF_DAY.sub(repl, text)
    text = re.sub(r"\b(?:в\s+)?полтора\s+дня\b", "в 13:30", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:в\s+)?полдня\b", "в 13:00", text, flags=re.IGNORECASE)
    text = re.sub(r"\bв\s+полдень\b", "в 12:00", text, flags=re.IGNORECASE)
    text = re.sub(r"\bполдень\b", "12:00", text, flags=re.IGNORECASE)
    text = re.sub(r"\bв\s+полночь\b", "в 00:00", text, flags=re.IGNORECASE)
    text = re.sub(r"\bполночь\b", "00:00", text, flags=re.IGNORECASE)
    text = re.sub(r"\bв\s+обед\b", "в 13:00", text, flags=re.IGNORECASE)
    return text


def normalize_bare_hours(text: str) -> str:
    def repl(match: re.Match) -> str:
        hour_value = _parse_hour_token(match.group(2))
        if hour_value is None:
            return match.group(0)
        return f"{match.group(1)}{hour_value}:00{match.group(3)}"

    return BARE_HOUR.sub(repl, text)


def normalize_comma_hours(text: str) -> str:
    """«в 10, 16 и 21» → «в 10:00, 16:00 и 21:00»."""

    def expand(match: re.Match) -> str:
        hours = [int(x) for x in re.findall(r"\d{1,2}", match.group(0))]
        if len(hours) < 2:
            return match.group(0)
        formatted = [f"{h}:00" for h in hours]
        if re.search(r"\s+и\s+", match.group(0)):
            if len(formatted) == 2:
                return f"в {formatted[0]} и {formatted[1]}"
            return "в " + ", ".join(formatted[:-1]) + " и " + formatted[-1]
        return "в " + ", ".join(formatted)

    pattern = re.compile(
        r"\bв\s+\d{1,2}(?:\s*[,]\s*\d{1,2}|\s+и\s+(?:в\s+)?\d{1,2})+\b",
        re.IGNORECASE,
    )
    return pattern.sub(expand, text)


def normalize_phrase(text: str) -> str:
    text = re.sub(
        r"^(?:еженедельно|раз\s+в\s+неделю|каждую\s+неделю)\s+",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )
    text = normalize_time_dots(text)
    text = normalize_spaced_time(text)
    text = normalize_spoken_zero_time(text)
    text = normalize_k_time(text)
    text = normalize_half_ordinal(text)
    text = normalize_part_of_day(text)
    text = normalize_comma_hours(text)
    return normalize_bare_hours(text)


parse_number_token = _parse_hour_token


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


def _build_named_date(now: datetime, day: int, month: int, hour: int, minute: int) -> datetime:
    year = now.year
    max_day = calendar.monthrange(year, month)[1]
    safe_day = min(day, max_day)
    candidate = now.replace(
        year=year, month=month, day=safe_day, hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate <= now:
        year += 1
        max_day = calendar.monthrange(year, month)[1]
        safe_day = min(day, max_day)
        candidate = candidate.replace(year=year, day=safe_day)
    return candidate


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

    if match := NAMED_DATE_AT_TIME.search(normalized):
        day = int(match.group("d"))
        month = MONTH_GENITIVE[match.group("month").lower()]
        hour, minute = int(match.group("h")), int(match.group("m"))
        if 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59:
            run_at = _build_named_date(now, day, month, hour, minute)
            task = _extract_task(normalized, match)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    if match := NAMED_DATE.search(normalized):
        day = int(match.group("d"))
        month_key = match.group("month").lower()
        if month_key in MONTH_GENITIVE and 1 <= day <= 31:
            month = MONTH_GENITIVE[month_key]
            run_at = _build_named_date(now, day, month, DEFAULT_DAY_HOUR, DEFAULT_DAY_MINUTE)
            task = _extract_task(normalized, match)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    for pattern in (DAY_AT_TIME, TIME_THEN_DAY):
        if match := pattern.search(normalized):
            day = match.group("day")
            hour, minute = int(match.group("h")), int(match.group("m"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                continue
            run_at = _build_run_at(now, _day_offset(day), hour, minute)
            task = _extract_task(normalized, match)
            return ParsedReminder(text=task, kind="once", run_at=run_at)

    if match := DAY_PART_PERIOD.search(normalized):
        day = match.group("day")
        part_key = _normalize_part_token(match.group("part"))
        hour = PART_DEFAULT_HOUR.get(part_key, DEFAULT_DAY_HOUR)
        run_at = _build_run_at(now, _day_offset(day), hour, 0)
        task = _extract_task(normalized, match)
        return ParsedReminder(text=task, kind="once", run_at=run_at)

    for pattern in (DAY_ONLY_PREFIX, DAY_ONLY_SUFFIX):
        if match := pattern.match(normalized):
            task_raw = match.group("task")
            if TIME_IN_TASK.search(task_raw):
                continue
            day = match.group("day")
            task = NOISE_PREFIX.sub("", task_raw).strip()
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
