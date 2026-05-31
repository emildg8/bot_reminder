"""Кратковременное хранение задачи без времени (для кнопок «когда напомнить»)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

TASK_PENDING_TTL = timedelta(minutes=30)


@dataclass
class PendingTask:
    text: str
    created_at: datetime
    edit_reminder_id: int | None = None
    ambiguous_day: str | None = None
    ambiguous_hour: int | None = None


_pending: dict[int, PendingTask] = {}


def store_pending_task(
    user_id: int,
    task: str,
    *,
    edit_reminder_id: int | None = None,
    ambiguous_day: str | None = None,
    ambiguous_hour: int | None = None,
) -> None:
    _prune()
    _pending[user_id] = PendingTask(
        text=task.strip(),
        created_at=datetime.now(timezone.utc),
        edit_reminder_id=edit_reminder_id,
        ambiguous_day=ambiguous_day,
        ambiguous_hour=ambiguous_hour,
    )


def pop_pending_task(user_id: int) -> PendingTask | None:
    entry = _pending.pop(user_id, None)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > TASK_PENDING_TTL:
        return None
    return entry


def get_pending_task(user_id: int) -> PendingTask | None:
    entry = _pending.get(user_id)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > TASK_PENDING_TTL:
        _pending.pop(user_id, None)
        return None
    return entry


def prune_expired_pending_tasks() -> int:
    now = datetime.now(timezone.utc)
    removed = 0
    for uid, entry in list(_pending.items()):
        if now - entry.created_at > TASK_PENDING_TTL:
            _pending.pop(uid, None)
            removed += 1
    return removed


def _prune() -> None:
    prune_expired_pending_tasks()
