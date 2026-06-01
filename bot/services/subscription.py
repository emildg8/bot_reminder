"""Free / Pro лимиты и сообщения (выключено по умолчанию — MONETIZATION_ENABLED)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import User
from bot.db.repository import count_active_reminders_for_user
from bot.services.admin_access import is_bot_admin


def monetization_active() -> bool:
    return settings.monetization_enabled


def is_pro_user(user: User | None, telegram_id: int) -> bool:
    if not monetization_active():
        return True
    if is_bot_admin(telegram_id):
        return True
    return bool(user and user.is_pro)


async def can_add_reminder(session: AsyncSession, telegram_id: int) -> tuple[bool, int, int]:
    """(allowed, current_count, limit). limit=0 means unlimited."""
    if not monetization_active():
        return True, 0, 0

    from bot.db.repository import get_user_by_telegram_id

    user = await get_user_by_telegram_id(session, telegram_id)
    if is_pro_user(user, telegram_id):
        return True, 0, 0

    limit = settings.free_active_limit
    current = await count_active_reminders_for_user(session, telegram_id)
    return current < limit, current, limit


def format_limit_reached(current: int, limit: int) -> str:
    return (
        f"📊 Достигнут лимит бесплатного тарифа: <b>{current}/{limit}</b> активных напоминаний.\n\n"
        "Pro снимает лимит · группы · приоритет.\n"
        "Подробнее: /subscribe"
    )


def format_subscribe_message(*, current: int = 0, limit: int | None = None) -> str:
    limit = limit or settings.free_active_limit
    pro_line = settings.pro_contact_hint
    return (
        "⭐ <b>Pro</b>\n\n"
        f"Free: до <b>{limit}</b> активных напоминаний"
        + (f" (сейчас {current})" if current else "")
        + ".\n"
        "Pro: без лимита, приоритет поддержки.\n\n"
        f"{pro_line}\n\n"
        "Статус: /status"
    )


def format_monetization_disabled() -> str:
    return (
        "⭐ <b>Pro</b> — в разработке.\n\n"
        "Сейчас все функции бесплатны, без лимитов.\n"
        "Следи за обновлениями в /about."
    )
