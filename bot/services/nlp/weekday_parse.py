import re
from datetime import time

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
    rf"\b(?:во?\s+)?(?P<day>{_DAY_TOKEN})\b"
    r"\s+(?:в\s+)?(\d{1,2})[:.](\d{2})\b",
    re.IGNORECASE,
)


def _remove_span(text: str, match: re.Match) -> str:
    return (text[: match.start()] + text[match.end() :]).strip(" ,.")


def _task_after_last_time(text: str, time_matches: list[re.Match]) -> str:
    if not time_matches:
        return "Напоминание"
    task = text[time_matches[-1].end() :].strip(" ,.—-")
    task = re.sub(r"^(?:и\s+)*(?:в\s+)?", "", task, flags=re.IGNORECASE).strip()
    return task or "Напоминание"


def parse_weekday_tokens(text: str) -> list[int]:
    normalized = text.lower()
    normalized = re.sub(r"[,]", " ", normalized)
    normalized = re.sub(r"\s+и\s+", " ", normalized)
    normalized = re.sub(r"^(?:во|в|по)\s+", "", normalized)
    tokens = [t for t in normalized.split() if t]
    weekdays: list[int] = []
    for token in tokens:
        key = token.strip(".")
        if key in WEEKDAY_MAP:
            weekdays.append(WEEKDAY_MAP[key])
    return sorted(set(weekdays))


def _weekdays_before_times(text: str, time_matches: list[re.Match]) -> list[int]:
    if not time_matches:
        return parse_weekday_tokens(text)
    chunk = text[: time_matches[-1].start()]
    weekdays = parse_weekday_tokens(chunk)
    if weekdays:
        return weekdays
    return parse_weekday_tokens(text)


DEFAULT_WEEKLY_HOUR = 9
DEFAULT_WEEKLY_MINUTE = 0


def find_weekly_schedules(text: str) -> list[tuple[list[int], int, int, str]]:
    """Несколько расписаний: одни дни недели × несколько времён."""
    if match := EACH_WEEKDAY_PATTERN.search(text):
        day_token = match.group("day").lower()
        weekdays = parse_weekday_tokens(day_token)
        if not weekdays:
            return []
        time_matches = list(TIME_PATTERN.finditer(text, match.end()))
        if time_matches:
            task = _task_after_last_time(text, time_matches)
            return [
                (weekdays, int(tm.group(1)), int(tm.group(2)), task)
                for tm in time_matches
            ]
        task_text = _remove_span(text, match)
        if not task_text:
            task_text = text[match.end() :].strip(" ,.")
        return [
            (weekdays, DEFAULT_WEEKLY_HOUR, DEFAULT_WEEKLY_MINUTE, task_text or "Напоминание")
        ]

    time_matches = list(TIME_PATTERN.finditer(text))
    if time_matches:
        weekdays = _weekdays_before_times(text, time_matches)
        if weekdays:
            task = _task_after_last_time(text, time_matches)
            return [
                (weekdays, int(tm.group(1)), int(tm.group(2)), task)
                for tm in time_matches
            ]

    if match := IN_WEEKDAY_PATTERN.search(text):
        day_token = match.group("day").lower()
        hour, minute = int(match.group(2)), int(match.group(3))
        time_matches = list(TIME_PATTERN.finditer(text, match.end()))
        weekdays = _weekdays_before_times(text, [match, *time_matches])
        if not weekdays:
            weekdays = parse_weekday_tokens(day_token)
        if not weekdays:
            return []
        if len(time_matches) > 1:
            task = _task_after_last_time(text, time_matches)
            return [
                (weekdays, int(tm.group(1)), int(tm.group(2)), task)
                for tm in time_matches
            ]
        task_text = _remove_span(text, match).strip(" ,.")
        if not task_text:
            task_text = text[match.end() :].strip(" ,.")
        return [(weekdays, hour, minute, task_text or "Напоминание")]

    return []


def find_custom_weekly(text: str) -> tuple[list[int], int, int, str] | None:
    """Returns (weekdays, hour, minute, task_text) or None."""
    schedules = find_weekly_schedules(text)
    return schedules[0] if schedules else None


def schedules_to_parsed(text: str) -> list[tuple[list[int], time, str]]:
    return [
        (weekdays, time(hour, minute), task)
        for weekdays, hour, minute, task in find_weekly_schedules(text)
    ]
