import re

# 0=Mon .. 6=Sun (datetime.weekday())
WEEKDAY_MAP: dict[str, int] = {
    "пн": 0,
    "понедельник": 0,
    "понедельникам": 0,
    "вт": 1,
    "вторник": 1,
    "вторникам": 1,
    "ср": 2,
    "среда": 2,
    "средам": 2,
    "среду": 2,
    "чт": 3,
    "четверг": 3,
    "четвергам": 3,
    "пт": 4,
    "пятница": 4,
    "пятницам": 4,
    "пятницу": 4,
    "сб": 5,
    "суббота": 5,
    "субботам": 5,
    "субботу": 5,
    "вс": 6,
    "воскресенье": 6,
    "воскресеньям": 6,
}

# Длинные названия первыми + \b, чтобы «вт» не матчилось внутри «вторник»
_DAY_TOKEN = (
    r"понедельник\w*|вторник\w*|сред\w*|четверг\w*|"
    r"пятниц\w*|суббот\w*|воскресен\w*|"
    r"пн|вт|ср|чт|пт|сб|вс"
)

TIME_PATTERN = re.compile(r"(?:в\s+)?(\d{1,2})[:.](\d{2})")

EACH_WEEKDAY_PATTERN = re.compile(
    rf"кажды(?:й|ую|ое)\s+(?P<day>{_DAY_TOKEN})\b",
    re.IGNORECASE,
)

IN_WEEKDAY_PATTERN = re.compile(
    rf"\b(?:в\s+)?(?P<day>{_DAY_TOKEN})\b"
    r"\s+(?:в\s+)?(\d{1,2})[:.](\d{2})\b",
    re.IGNORECASE,
)


def _remove_span(text: str, match: re.Match) -> str:
    return (text[: match.start()] + text[match.end() :]).strip(" ,.")


def parse_weekday_tokens(text: str) -> list[int]:
    normalized = text.lower()
    normalized = re.sub(r"[,]", " ", normalized)
    normalized = re.sub(r"\s+и\s+", " ", normalized)
    tokens = [t for t in normalized.split() if t]
    weekdays: list[int] = []
    for token in tokens:
        key = token.strip(".")
        if key in WEEKDAY_MAP:
            weekdays.append(WEEKDAY_MAP[key])
    return sorted(set(weekdays))


DEFAULT_WEEKLY_HOUR = 9
DEFAULT_WEEKLY_MINUTE = 0


def find_custom_weekly(text: str) -> tuple[list[int], int, int, str] | None:
    """Returns (weekdays, hour, minute, task_text) or None."""
    if match := EACH_WEEKDAY_PATTERN.search(text):
        day_token = match.group("day").lower()
        time_match = TIME_PATTERN.search(text, match.end())
        weekdays = parse_weekday_tokens(day_token)
        if not weekdays:
            return None
        if time_match:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            task_text = _remove_span(text, match)
            task_text = TIME_PATTERN.sub("", task_text).strip(" ,.")
        else:
            hour, minute = DEFAULT_WEEKLY_HOUR, DEFAULT_WEEKLY_MINUTE
            task_text = _remove_span(text, match)
            if not task_text:
                task_text = text[match.end() :].strip(" ,.")
        return weekdays, hour, minute, task_text or "Напоминание"

    time_match = TIME_PATTERN.search(text)
    if time_match:
        before = text[: time_match.start()]
        weekdays = parse_weekday_tokens(before)
        if weekdays:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            task_text = text[time_match.end() :].strip(" ,.")
            if not task_text:
                task_text = re.sub(r"(?:по\s+)?", "", before).strip(" ,.")
            return weekdays, hour, minute, task_text

    if match := IN_WEEKDAY_PATTERN.search(text):
        day_token = match.group("day").lower()
        hour, minute = int(match.group(2)), int(match.group(3))
        weekdays = parse_weekday_tokens(day_token)
        if not weekdays:
            return None
        task_text = _remove_span(text, match).strip(" ,.")
        if not task_text:
            task_text = text[match.end() :].strip(" ,.")
        return weekdays, hour, minute, task_text

    return None
