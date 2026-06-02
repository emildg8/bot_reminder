"""Telegram Stars — добровольная благодарность автору."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from bot.config import settings
from bot.db.repository import async_session, record_star_payment
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.stars_tips import (
    format_thank_you,
    format_thank_you_duplicate,
    parse_tip_payload,
    tip_invoice_prices,
    tip_payload,
    tips_enabled,
)

logger = logging.getLogger(__name__)

router = Router()


async def _notify_admins_tip(bot, user_id: int, amount: int, username: str | None) -> None:
    if not settings.stars_tips_notify_admin:
        return
    uname = f"@{username}" if username else "—"
    text = f"⭐ <b>+{amount}</b> Stars · <code>{user_id}</code> {uname}"
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
    if amount not in settings.stars_tip_preset_list():
        await callback.answer("Неверная сумма", show_alert=True)
        return
    user_id = callback.from_user.id
    await callback.answer()
    await callback.bot.send_invoice(
        chat_id=user_id,
        title="Благодарность автору",
        description="Добровольная поддержка разработчика бота",
        payload=tip_payload(user_id, amount),
        provider_token="",
        currency="XTR",
        prices=tip_invoice_prices(amount),
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    if not tips_enabled():
        await query.answer(ok=False, error_message="Stars временно недоступны")
        return
    parsed = parse_tip_payload(query.invoice_payload or "")
    if parsed is None:
        await query.answer(ok=False, error_message="Неизвестный платёж")
        return
    user_id, _amount = parsed
    if user_id != query.from_user.id:
        await query.answer(ok=False, error_message="Платёж привязан к другому пользователю")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    if not tips_enabled():
        return
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
    if recorded is None:
        await message.answer(
            format_thank_you_duplicate(),
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    await message.answer(
        format_thank_you(amount),
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )
    await _notify_admins_tip(
        message.bot,
        user_id,
        amount,
        message.from_user.username,
    )
    logger.info("Stars tip %s from user %s", amount, user_id)
