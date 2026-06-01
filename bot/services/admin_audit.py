"""Кольцевой журнал действий администраторов (in-memory)."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 40
_log: deque[tuple[datetime, int, str]] = deque(maxlen=_MAX_ENTRIES)


def log_admin_action(admin_id: int, action: str) -> None:
    entry = (datetime.now(timezone.utc), admin_id, action)
    _log.append(entry)
    logger.info("admin %s: %s", admin_id, action)


def format_admin_log(limit: int = 15) -> str:
    if not _log:
        return "📜 <b>Журнал админ-действий</b>\n\nПока пуст (после рестарта бота сбрасывается)."
    lines = ["📜 <b>Журнал админ-действий</b> (последние)\n"]
    for when, admin_id, action in list(_log)[-limit:][::-1]:
        ts = when.strftime("%d.%m %H:%M")
        lines.append(f"• <code>{ts}</code> · <code>{admin_id}</code>\n  {action}")
    return "\n".join(lines)
