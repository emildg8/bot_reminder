"""Telegram Stars — оплата Pro."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, record_star_payment, set_user_pro
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.subscription import (
    compute_pro_expiry,
    format_subscribe_message,
    is_pro_user,
    monetization_active,
    pro_invoice_payload,
    pro_invoice_prices,
    pro_expires_label,
    stars_payments_active,
    subscribe_keyboard,
)

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "pay:pro")
async def cb_pay_pro(callback: CallbackQuery) -> None:
    if not stars_payments_active():
        await callback.answer("Оплата Stars выключена", show_alert=True)
        return
    user_id = callback.from_user.id
    await callback.answer()
    await callback.bot.send_invoice(
        chat_id=user_id,
        title="Pro подписка",
        description=(
            f"Pro на {settings.pro_duration_days} дней — без лимита активных напоминаний."
        ),
        payload=pro_invoice_payload(user_id),
        provider_token="",
        currency="XTR",
        prices=pro_invoice_prices(),
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    if not stars_payments_active():
        await query.answer(ok=False, error_message="Оплата временно недоступна")
        return
    payload = query.invoice_payload or ""
    if not payload.startswith("pro:"):
        await query.answer(ok=False, error_message="Неизвестный товар")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    if not monetization_active():
        return
    payment = message.successful_payment
    if payment is None or payment.currency != "XTR":
        return

    charge_id = payment.telegram_payment_charge_id
    user_id = message.from_user.id
    async with async_session() as session:
        recorded = await record_star_payment(
            session,
            user_telegram_id=user_id,
            charge_id=charge_id,
            stars_amount=payment.total_amount,
        )
        if recorded is None:
            await message.answer("✅ Pro уже активирован по этому платежу.")
            return
        expires = compute_pro_expiry()
        await get_or_create_user(session, user_id, settings.default_timezone)
        await set_user_pro(session, user_id, is_pro=True, pro_expires_at=expires)

    exp_label = expires.strftime("%d.%m.%Y")
    await message.answer(
        f"⭐ <b>Pro активирован</b> до <b>{exp_label}</b>.\n"
        "Лимит активных напоминаний снят · /status",
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )
    logger.info("Stars Pro granted to %s until %s", user_id, exp_label)


async def send_subscribe_with_payment(message: Message, *, current: int) -> None:
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, settings.default_timezone)
        if is_pro_user(user, message.from_user.id):
            exp = pro_expires_label(user)
            extra = f" до <b>{exp}</b>" if exp else ""
            await message.answer(
                f"⭐ У тебя уже <b>Pro</b>{extra} — лимит активных напоминаний снят.",
                reply_markup=menu_keyboard_for_chat(message.chat.id),
            )
            return

    await message.answer(
        format_subscribe_message(current=current, limit=settings.free_active_limit),
        reply_markup=subscribe_keyboard(),
    )
