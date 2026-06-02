"""Ожидание выбора assignee при нескольких @user без времени в фразе."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from bot.services.chat_ctx import ChatKind
from bot.services.nlp.schemas import ParsedReminder

ASSIGNEE_PENDING_TTL = timedelta(minutes=15)


@dataclass
class PendingAssigneeCreate:
    user_id: int
    parsed_items: list[ParsedReminder]
    phrase: str
    candidates: tuple[str, ...]
    timezone: str
    delivery_chat_id: int
    source_label: str
    heard_text: str
    collective_chat_id: int | None
    collective_chat_kind: ChatKind | None
    created_at: datetime


_pending: dict[int, PendingAssigneeCreate] = {}


def store_pending_assignee(entry: PendingAssigneeCreate) -> None:
    prune_expired_pending_assignee()
    _pending[entry.user_id] = entry


def pop_pending_assignee(user_id: int) -> PendingAssigneeCreate | None:
    entry = _pending.pop(user_id, None)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > ASSIGNEE_PENDING_TTL:
        return None
    return entry


def clear_pending_assignee(user_id: int) -> None:
    _pending.pop(user_id, None)


def get_pending_assignee(user_id: int) -> PendingAssigneeCreate | None:
    entry = _pending.get(user_id)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > ASSIGNEE_PENDING_TTL:
        _pending.pop(user_id, None)
        return None
    return entry


def prune_expired_pending_assignee() -> int:
    now = datetime.now(timezone.utc)
    removed = 0
    for uid, entry in list(_pending.items()):
        if now - entry.created_at > ASSIGNEE_PENDING_TTL:
            _pending.pop(uid, None)
            removed += 1
    return removed
