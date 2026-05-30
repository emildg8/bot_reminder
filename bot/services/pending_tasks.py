"""Кратковременное хранение задачи без времени (для кнопок «когда напомнить»)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

TASK_PENDING_TTL = timedelta(minutes=30)


@dataclass
class PendingTask:
    text: str
    created_at: datetime


_pending: dict[int, PendingTask] = {}


def store_pending_task(user_id: int, task: str) -> None:
    _prune()
    _pending[user_id] = PendingTask(
        text=task.strip(),
        created_at=datetime.now(timezone.utc),
    )


def pop_pending_task(user_id: int) -> str | None:
    entry = _pending.pop(user_id, None)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > TASK_PENDING_TTL:
        return None
    return entry.text


def get_pending_task(user_id: int) -> str | None:
    entry = _pending.get(user_id)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > TASK_PENDING_TTL:
        _pending.pop(user_id, None)
        return None
    return entry.text


def _prune() -> None:
    now = datetime.now(timezone.utc)
    for uid, entry in list(_pending.items()):
        if now - entry.created_at > TASK_PENDING_TTL:
            _pending.pop(uid, None)
