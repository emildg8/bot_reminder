from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.repository import (
    async_session,
    count_user_star_tips,
    get_user_by_telegram_id,
    set_user_tip_nudge_dismissed,
)
from bot.keyboards.reply import MENU_BUTTON_TEXTS, menu_keyboard_for_chat
from bot.services.stars_tips import (
    custom_amount_confirm_keyboard,
    custom_amount_keyboard,
    deliver_tip_invoice,
    format_amount_out_of_range,
    format_custom_amount_confirm,
    format_custom_amount_invalid,
    format_custom_amount_pending_hint,
    format_custom_amount_prompt,
    format_thanks_screen,
    format_tips_disabled,
    is_valid_tip_amount,
    looks_like_tip_amount,
    parse_tip_amount_input,
    tip_keyboard,
    tips_enabled,
    text_has_letters,
    user_had_pro,
)
from bot.services.tip_custom_state import (
    clear_all_tip_custom,
    clear_custom_amount,
    get_pending_confirm,
    is_pending_confirm,
    is_waiting_custom_amount,
    set_pending_confirm,
    start_custom_amount,
)

router = Router()


async def _prior_tips(user_id: int) -> tuple[int, int] | None:
    async with async_session() as session:
        return await count_user_star_tips(session, user_id)


async def send_thanks_screen(
    message: Message,
    *,
    subscribe_redirect: bool = False,
) -> None:
    kb = menu_keyboard_for_chat(message.chat.id)
    if not tips_enabled():
        await message.answer(
            format_tips_disabled(from_subscribe=subscribe_redirect),
            reply_markup=kb,
        )
        return
    prior = None
    if message.from_user:
        prior = await _prior_tips(message.from_user.id)
    await message.answer(
        format_thanks_screen(subscribe_redirect=subscribe_redirect, prior_tips=prior),
        reply_markup=tip_keyboard(),
    )


@router.message(Command("thanks", "support"))
async def cmd_thanks(message: Message) -> None:
    clear_all_tip_custom(message.from_user.id)
    await send_thanks_screen(message)


@router.message(Command("subscribe"))
async def cmd_subscribe_redirect(message: Message) -> None:
    clear_all_tip_custom(message.from_user.id)
    subscribe_redirect = False
    if message.from_user:
        async with async_session() as session:
            user = await get_user_by_telegram_id(session, message.from_user.id)
            if user is not None and user_had_pro(user):
                subscribe_redirect = True
    await send_thanks_screen(message, subscribe_redirect=subscribe_redirect)


@router.callback_query(F.data == "tip:custom")
async def cb_tip_custom(callback: CallbackQuery) -> None:
    if not tips_enabled():
        await callback.answer("Stars сейчас недоступны", show_alert=True)
        return
    start_custom_amount(callback.from_user.id)
    await callback.answer()
    await callback.message.answer(
        format_custom_amount_prompt(),
        reply_markup=custom_amount_keyboard(),
    )


@router.callback_query(F.data.startswith("tip:confirm:"))
async def cb_tip_confirm(callback: CallbackQuery) -> None:
    if not tips_enabled():
        await callback.answer("Stars сейчас недоступны", show_alert=True)
        return
    raw = (callback.data or "").removeprefix("tip:confirm:")
    if not raw.isdigit():
        await callback.answer("Ошибка", show_alert=True)
        return
    amount = int(raw)
    pending = get_pending_confirm(callback.from_user.id)
    if pending is None or pending != amount:
        await callback.answer("Подтверждение устарело — выбери сумму снова", show_alert=True)
        return
    if not is_valid_tip_amount(amount):
        await callback.answer("Неверная сумма", show_alert=True)
        return
    clear_all_tip_custom(callback.from_user.id)
    await callback.answer(f"Счёт на {amount} ⭐")
    await deliver_tip_invoice(
        callback.bot,
        user_id=callback.from_user.id,
        amount=amount,
        reply_chat_id=callback.message.chat.id,
    )


@router.callback_query(F.data == "tip:back")
async def cb_tip_back(callback: CallbackQuery) -> None:
    clear_all_tip_custom(callback.from_user.id)
    await callback.answer()
    await send_thanks_screen(callback.message)


@router.callback_query(F.data == "tip:nudge:dismiss")
async def cb_tip_nudge_dismiss(callback: CallbackQuery) -> None:
    async with async_session() as session:
        await set_user_tip_nudge_dismissed(session, callback.from_user.id)
    await callback.answer("Ок")
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTON_TEXTS))
async def handle_custom_tip_amount(message: Message) -> None:
    if not tips_enabled():
        return
    user_id = message.from_user.id
    text = message.text or ""

    if is_pending_confirm(user_id):
        if text_has_letters(text):
            clear_all_tip_custom(user_id)
            return
        await message.answer(format_custom_amount_pending_hint())
        return

    if not is_waiting_custom_amount(user_id):
        return

    if text_has_letters(text) or not looks_like_tip_amount(text):
        clear_custom_amount(user_id)
        return
    amount = parse_tip_amount_input(text)
    if amount is None:
        await message.answer(format_custom_amount_invalid(text))
        return
    if not is_valid_tip_amount(amount):
        await message.answer(format_amount_out_of_range(amount))
        return
    set_pending_confirm(user_id, amount)
    await message.answer(
        format_custom_amount_confirm(amount),
        reply_markup=custom_amount_confirm_keyboard(amount),
    )
