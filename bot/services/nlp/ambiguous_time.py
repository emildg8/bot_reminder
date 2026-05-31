"""Двусмысленное время: «завтра в 2» и «завтра созвон» без явного времени."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bot.services.nlp.absolute_time_parse import (
    DAY_ONLY_PREFIX,
    DAY_ONLY_SUFFIX,
    DAY_PART_PERIOD,
    HOUR_PART_OF_DAY,
    HOUR_WORD_PATTERN,
    NOISE_PREFIX,
    TIME_IN_TASK,
    _parse_hour_token,
)

_DAY = r"сегодня|завтра|послезавтра|после\s+завтра"
_AMBIGUOUS = re.compile(
    rf"^(?P<day>{_DAY})\s+(?:в\s+)?(?P<h>{HOUR_WORD_PATTERN}|\d{{1,2}})\s+(?P<task>.+)$",
    re.IGNORECASE,
)
_AMBIGUOUS_SUFFIX = re.compile(
    rf"^(?P<task>.+?)\s+(?P<day>{_DAY})\s+(?:в\s+)?(?P<h>{HOUR_WORD_PATTERN}|\d{{1,2}})\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AmbiguousDayHour:
    day: str
    hour: int
    task: str


@dataclass(frozen=True)
class AmbiguousDayOnly:
    day: str
    task: str


def _match_ambiguous_day_hour(phrase: str) -> re.Match[str] | None:
    match = _AMBIGUOUS.match(phrase)
    if match:
        return match
    return _AMBIGUOUS_SUFFIX.match(phrase)


def detect_ambiguous_day_hour(text: str) -> AmbiguousDayHour | None:
    phrase = NOISE_PREFIX.sub("", text.strip()).strip()
    if not phrase or HOUR_PART_OF_DAY.search(phrase):
        return None
    if re.search(r"\d{1,2}[:.]\d{2}", phrase):
        return None
    match = _match_ambiguous_day_hour(phrase)
    if not match:
        return None
    hour = _parse_hour_token(match.group("h"))
    if hour is None or not (1 <= hour <= 11):
        return None
    day = match.group("day").lower().replace("после завтра", "послезавтра")
    task = match.group("task").strip()
    if not task:
        return None
    return AmbiguousDayHour(day=day, hour=hour, task=task)


def detect_ambiguous_day_only(text: str) -> AmbiguousDayOnly | None:
    phrase = NOISE_PREFIX.sub("", text.strip()).strip()
    if not phrase or detect_ambiguous_day_hour(phrase):
        return None
    if DAY_PART_PERIOD.search(phrase) or HOUR_PART_OF_DAY.search(phrase):
        return None
    for pattern in (DAY_ONLY_PREFIX, DAY_ONLY_SUFFIX):
        match = pattern.match(phrase)
        if not match:
            continue
        task_raw = match.group("task")
        if TIME_IN_TASK.search(task_raw) or HOUR_PART_OF_DAY.search(task_raw):
            return None
        day = match.group("day").lower().replace("после завтра", "послезавтра")
        task = NOISE_PREFIX.sub("", task_raw).strip()
        task = re.sub(r"\s+", " ", task)
        if not task:
            return None
        return AmbiguousDayOnly(day=day, task=task)
    return None


def phrase_from_ambiguous_choice(*, task: str, day: str, hour: int, choice: str) -> str:
    if choice == "morn":
        return f"{day} в 9:00 {task}"
    if choice == "day":
        resolved = hour + 12 if 1 <= hour <= 11 else hour
        return f"{day} в {resolved:02d}:00 {task}"
    if choice == "night":
        return f"{day} в {hour:02d}:00 {task}"
    return f"{day} в 9:00 {task}"


def phrase_from_day_only_choice(*, task: str, day: str, choice: str) -> str:
    hours = {"morn": "9:00", "day": "14:00", "night": "18:00"}
    hour = hours.get(choice, "9:00")
    return f"{day} в {hour} {task}"
