"""Free / Pro лимиты, Telegram Stars и сообщения."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import User
from bot.db.repository import count_active_reminders_for_user
from bot.services.admin_access import is_bot_admin


def monetization_active() -> bool:
    return settings.monetization_enabled


def stars_payments_active() -> bool:
    return monetization_active() and settings.stars_payments_enabled


def _pro_not_expired(user: User | None) -> bool:
    if user is None or not user.is_pro:
        return False
    if user.pro_expires_at is None:
        return True
    return user.pro_expires_at.astimezone(timezone.utc) > datetime.now(timezone.utc)


def is_pro_user(user: User | None, telegram_id: int) -> bool:
    if not monetization_active():
        return True
    if is_bot_admin(telegram_id):
        return True
    return _pro_not_expired(user)


def pro_expires_label(user: User | None) -> str | None:
    if user is None or not user.pro_expires_at:
        return None
    exp = user.pro_expires_at.astimezone(timezone.utc)
    return exp.strftime("%d.%m.%Y")


def compute_pro_expiry(from_dt: datetime | None = None) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    return base + timedelta(days=settings.pro_duration_days)


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
    stars = (
        "\n\n⭐ Купить Pro: /subscribe"
        if stars_payments_active()
        else ""
    )
    return (
        f"📊 Достигнут лимит бесплатного тарифа: <b>{current}/{limit}</b> активных напоминаний.\n\n"
        "Pro снимает лимит · группы · приоритет.\n"
        "Подробнее: /subscribe"
        f"{stars}"
    )


def subscribe_keyboard() -> InlineKeyboardMarkup | None:
    if not stars_payments_active():
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ Купить Pro — {settings.pro_stars_price} Stars",
                    callback_data="pay:pro",
                )
            ]
        ]
    )


def format_subscribe_message(*, current: int = 0, limit: int | None = None) -> str:
    limit = limit or settings.free_active_limit
    if stars_payments_active():
        pro_line = (
            f"Оплата Stars: <b>{settings.pro_stars_price} ⭐</b> "
            f"на <b>{settings.pro_duration_days}</b> дн."
        )
    else:
        pro_line = settings.pro_contact_hint
    return (
        "⭐ <b>Pro</b>\n\n"
        f"Free: до <b>{limit}</b> активных напоминаний"
        + (f" (сейчас {current})" if current else "")
        + ".\n"
        f"Pro: без лимита на {settings.pro_duration_days} дн., приоритет поддержки.\n\n"
        f"{pro_line}\n\n"
        "Статус: /status"
    )


def format_monetization_disabled() -> str:
    return (
        "⭐ <b>Pro</b> — в разработке.\n\n"
        "Сейчас все функции бесплатны, без лимитов.\n"
        "Следи за обновлениями в /about."
    )


def pro_invoice_prices() -> list[LabeledPrice]:
    return [LabeledPrice(label="Pro", amount=settings.pro_stars_price)]


def pro_invoice_payload(user_id: int) -> str:
    return f"pro:{user_id}"
