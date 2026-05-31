"""Двусмысленное время «завтра в 2» без «дня/утра/ночи»."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bot.services.nlp.absolute_time_parse import HOUR_PART_OF_DAY, HOUR_WORD_PATTERN, _parse_hour_token

_DAY = r"сегодня|завтра|послезавтра|после\s+завтра"
_AMBIGUOUS = re.compile(
    rf"^(?P<day>{_DAY})\s+(?:в\s+)?(?P<h>{HOUR_WORD_PATTERN}|\d{{1,2}})\s+(?P<task>.+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AmbiguousDayHour:
    day: str
    hour: int
    task: str


def detect_ambiguous_day_hour(text: str) -> AmbiguousDayHour | None:
    phrase = text.strip()
    if not phrase or HOUR_PART_OF_DAY.search(phrase):
        return None
    if re.search(r"\d{1,2}[:.]\d{2}", phrase):
        return None
    match = _AMBIGUOUS.match(phrase)
    if not match:
        return None
    hour = _parse_hour_token(match.group("h"))
    if hour is None or not (1 <= hour <= 11):
        return None
    day = match.group("day").lower().replace("после завтра", "послезавтра")
    return AmbiguousDayHour(day=day, hour=hour, task=match.group("task").strip())


def phrase_from_ambiguous_choice(*, task: str, day: str, hour: int, choice: str) -> str:
    if choice == "morn":
        return f"{day} в 9:00 {task}"
    if choice == "day":
        resolved = hour + 12 if 1 <= hour <= 11 else hour
        return f"{day} в {resolved:02d}:00 {task}"
    if choice == "night":
        return f"{day} в {hour:02d}:00 {task}"
    return f"{day} в 9:00 {task}"
