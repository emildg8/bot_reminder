"""Ожидание ввода и подтверждения своей суммы Stars."""

from __future__ import annotations

import time

TTL_SECONDS = 300

_waiting: dict[int, float] = {}
_confirm: dict[int, tuple[int, float]] = {}


def _expired(updated_at: float) -> bool:
    return time.time() - updated_at > TTL_SECONDS


def start_custom_amount(user_id: int) -> None:
    clear_all_tip_custom(user_id)
    _waiting[user_id] = time.time()


def is_waiting_custom_amount(user_id: int) -> bool:
    started = _waiting.get(user_id)
    if started is None:
        return False
    if _expired(started):
        _waiting.pop(user_id, None)
        return False
    return True


def set_pending_confirm(user_id: int, amount: int) -> None:
    _waiting.pop(user_id, None)
    _confirm[user_id] = (amount, time.time())


def get_pending_confirm(user_id: int) -> int | None:
    pending = _confirm.get(user_id)
    if pending is None:
        return None
    amount, updated_at = pending
    if _expired(updated_at):
        _confirm.pop(user_id, None)
        return None
    return amount


def is_pending_confirm(user_id: int) -> bool:
    return get_pending_confirm(user_id) is not None


def clear_custom_amount(user_id: int) -> None:
    _waiting.pop(user_id, None)


def clear_pending_confirm(user_id: int) -> None:
    _confirm.pop(user_id, None)


def clear_all_tip_custom(user_id: int) -> None:
    clear_custom_amount(user_id)
    clear_pending_confirm(user_id)


def prune_expired_custom_amount() -> int:
    now = time.time()
    removed = 0
    for uid, started in list(_waiting.items()):
        if now - started > TTL_SECONDS:
            _waiting.pop(uid, None)
            removed += 1
    for uid, (_, started) in list(_confirm.items()):
        if now - started > TTL_SECONDS:
            _confirm.pop(uid, None)
            removed += 1
    return removed
