"""Настройки пользователя — snooze и пресеты."""

from __future__ import annotations

from bot.db.models import User

DEFAULT_SNOOZE_PRESETS = [5, 15, 30, 60, 180, 240]
DEFAULT_SNOOZE_STEP = 15
MIN_SNOOZE_MINUTES = 5
MAX_SNOOZE_MINUTES = 24 * 60


def parse_snooze_presets(raw: str | None) -> list[int]:
    if not raw:
        return list(DEFAULT_SNOOZE_PRESETS)
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            minutes = int(part)
        except ValueError:
            continue
        if MIN_SNOOZE_MINUTES <= minutes <= MAX_SNOOZE_MINUTES:
            values.append(minutes)
    return sorted(set(values)) or list(DEFAULT_SNOOZE_PRESETS)


def get_snooze_presets(user: User | None) -> list[int]:
    if user is None:
        return list(DEFAULT_SNOOZE_PRESETS)
    return parse_snooze_presets(user.snooze_presets)


def get_snooze_step(user: User | None) -> int:
    if user is None or user.snooze_step < MIN_SNOOZE_MINUTES:
        return DEFAULT_SNOOZE_STEP
    return min(user.snooze_step, MAX_SNOOZE_MINUTES)


def get_default_snooze_minutes(user: User | None) -> int:
    presets = get_snooze_presets(user)
    return presets[1] if len(presets) > 1 else presets[0]


def clamp_snooze_minutes(minutes: int) -> int:
    return max(MIN_SNOOZE_MINUTES, min(minutes, MAX_SNOOZE_MINUTES))


def format_snooze_minutes(minutes: int) -> str:
    if minutes % 60 == 0 and minutes >= 60:
        hours = minutes // 60
        if hours == 1:
            return "1 час"
        if 2 <= hours <= 4:
            return f"{hours} часа"
        return f"{hours} ч"
    return f"{minutes} мин"
