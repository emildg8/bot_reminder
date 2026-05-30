"""Состояние выбора времени для «Отложить»."""

from __future__ import annotations

import time
from dataclasses import dataclass

TTL_SECONDS = 600


@dataclass
class SnoozePickerState:
    reminder_id: int
    minutes: int
    updated_at: float


_states: dict[int, SnoozePickerState] = {}


def set_picker(user_id: int, reminder_id: int, minutes: int) -> None:
    _states[user_id] = SnoozePickerState(
        reminder_id=reminder_id,
        minutes=minutes,
        updated_at=time.time(),
    )


def get_picker(user_id: int, reminder_id: int) -> SnoozePickerState | None:
    state = _states.get(user_id)
    if state is None:
        return None
    if time.time() - state.updated_at > TTL_SECONDS:
        _states.pop(user_id, None)
        return None
    if state.reminder_id != reminder_id:
        return None
    return state


def update_minutes(user_id: int, reminder_id: int, minutes: int) -> SnoozePickerState | None:
    state = get_picker(user_id, reminder_id)
    if state is None:
        return None
    state.minutes = minutes
    state.updated_at = time.time()
    return state


def clear_picker(user_id: int) -> None:
    _states.pop(user_id, None)
