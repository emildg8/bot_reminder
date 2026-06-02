"""Telegram Stars — добровольная благодарность автору."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from bot.config import settings
from bot.db.repository import async_session, count_user_star_tips, record_star_payment
from bot.services.stars_tips import (
    deliver_tip_invoice,
    format_thank_you,
    format_thank_you_duplicate,
    is_tip_payload,
    is_valid_tip_amount,
    parse_tip_payload,
    pre_checkout_error,
    tip_thank_you_keyboard,
    tips_enabled,
)

logger = logging.getLogger(__name__)

router = Router()


async def _notify_admins_tip(
    bot,
    user_id: int,
    amount: int,
    *,
    username: str | None,
    first_name: str | None,
) -> None:
    if not settings.stars_tips_notify_admin:
        return
    uname = f"@{username}" if username else "—"
    who = first_name or uname
    text = f"⭐ <b>+{amount}</b> Stars · {who} · <code>{user_id}</code>"
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.warning("Cannot notify admin %s about tip: %s", admin_id, exc)


@router.callback_query(F.data.startswith("tip:pay:"))
async def cb_tip_pay(callback: CallbackQuery) -> None:
    if not tips_enabled():
        await callback.answer("Stars сейчас недоступны", show_alert=True)
        return
    raw = (callback.data or "").removeprefix("tip:pay:")
    if not raw.isdigit():
        await callback.answer("Ошибка", show_alert=True)
        return
    amount = int(raw)
    if not is_valid_tip_amount(amount):
        await callback.answer("Неверная сумма", show_alert=True)
        return
    user_id = callback.from_user.id
    await callback.answer(f"Счёт на {amount} ⭐")
    await deliver_tip_invoice(
        callback.bot,
        user_id=user_id,
        amount=amount,
        reply_chat_id=callback.message.chat.id,
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    payload = query.invoice_payload or ""
    if not is_tip_payload(payload):
        await query.answer(ok=True)
        return
    err = pre_checkout_error(
        payload,
        payer_id=query.from_user.id,
        total_amount=query.total_amount,
    )
    if err:
        await query.answer(ok=False, error_message=err)
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if payment is None or payment.currency != "XTR":
        return
    parsed = parse_tip_payload(payment.invoice_payload or "")
    if parsed is None:
        return
    user_id, amount = parsed
    if user_id != message.from_user.id or payment.total_amount != amount:
        return

    charge_id = payment.telegram_payment_charge_id
    async with async_session() as session:
        recorded = await record_star_payment(
            session,
            user_telegram_id=user_id,
            charge_id=charge_id,
            stars_amount=amount,
            kind="tip",
        )
        total_tips = None
        if recorded is not None:
            _, total_tips = await count_user_star_tips(session, user_id)
    if recorded is None:
        await message.answer(
            format_thank_you_duplicate(),
            reply_markup=tip_thank_you_keyboard(),
        )
        return

    await message.answer(
        format_thank_you(
            amount,
            first_name=message.from_user.first_name,
            total_tips=total_tips,
        ),
        reply_markup=tip_thank_you_keyboard(),
    )
    if settings.stars_tips_notify_admin:
        await _notify_admins_tip(
            message.bot,
            user_id,
            amount,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
    logger.info("Stars tip %s from user %s", amount, user_id)
