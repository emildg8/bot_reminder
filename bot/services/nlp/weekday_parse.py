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

TIME_PATTERN = re.compile(r"(?:в\s+)?(\d{1,2})[:.](\d{2})")

EACH_WEEKDAY_PATTERN = re.compile(
    r"кажды(?:й|ую|ое)\s+"
    r"(пн|вт|ср|чт|пт|сб|вс|понедельник\w*|вторник\w*|сред\w*|четверг\w*|пятниц\w*|суббот\w*|воскресен\w*)",
    re.IGNORECASE,
)


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


def find_custom_weekly(text: str) -> tuple[list[int], int, int, str] | None:
    """Returns (weekdays, hour, minute, task_text) or None."""
    if match := EACH_WEEKDAY_PATTERN.search(text):
        day_token = match.group(1).lower()
        time_match = TIME_PATTERN.search(text, match.end())
        if not time_match:
            return None
        hour, minute = int(time_match.group(1)), int(time_match.group(2))
        weekdays = parse_weekday_tokens(day_token)
        if not weekdays:
            return None
        task_text = EACH_WEEKDAY_PATTERN.sub("", text)
        task_text = TIME_PATTERN.sub("", task_text).strip(" ,.")
        return weekdays, hour, minute, task_text

    time_match = TIME_PATTERN.search(text)
    if not time_match:
        return None

    before = text[: time_match.start()]
    weekdays = parse_weekday_tokens(before)
    if len(weekdays) < 2:
        return None

    hour, minute = int(time_match.group(1)), int(time_match.group(2))
    task_text = text[time_match.end() :].strip(" ,.")
    if not task_text:
        task_text = re.sub(r"(?:по\s+)?", "", before).strip(" ,.")
    return weekdays, hour, minute, task_text
