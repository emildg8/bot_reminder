"""Поиск похожих активных напоминаний."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


async def find_duplicate_reminder(
    session: AsyncSession,
    chat_id: int,
    text: str,
    kind: str,
    *,
    created_by: int | None = None,
) -> Reminder | None:
    normalized = normalize_text(text)
    query = select(Reminder).where(
        Reminder.chat_id == chat_id,
        Reminder.is_active.is_(True),
        Reminder.kind == kind,
    )
    if created_by is not None:
        query = query.where(Reminder.created_by_telegram_id == created_by)

    result = await session.execute(query)
    for reminder in result.scalars().all():
        if normalize_text(reminder.text) == normalized:
            return reminder
    return None
