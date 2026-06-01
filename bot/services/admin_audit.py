"""Журнал действий администраторов (PostgreSQL / SQLite)."""

from __future__ import annotations

import logging
from datetime import timezone

from bot.db.repository import async_session, fetch_admin_actions, insert_admin_action

logger = logging.getLogger(__name__)


async def log_admin_action(admin_id: int, action: str) -> None:
    async with async_session() as session:
        await insert_admin_action(session, admin_id, action)
    logger.info("admin %s: %s", admin_id, action)


async def format_admin_log(limit: int = 15) -> str:
    async with async_session() as session:
        rows = await fetch_admin_actions(session, limit=limit)
    if not rows:
        return "📜 <b>Журнал админ-действий</b>\n\nПока пуст."
    lines = ["📜 <b>Журнал админ-действий</b> (последние)\n"]
    for row in rows:
        when = row.created_at.astimezone(timezone.utc)
        ts = when.strftime("%d.%m %H:%M")
        lines.append(f"• <code>{ts}</code> · <code>{row.admin_telegram_id}</code>\n  {row.action}")
    return "\n".join(lines)
