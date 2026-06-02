"""Добровольная благодарность автору через Telegram Stars."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

from bot.config import settings


def tips_enabled() -> bool:
    return settings.stars_tips_enabled


def tip_presets() -> list[int]:
    return settings.stars_tip_preset_list()


def tip_payload(user_id: int, amount: int) -> str:
    return f"tip:{user_id}:{amount}"


def parse_tip_payload(payload: str) -> tuple[int, int] | None:
    parts = (payload or "").split(":")
    if len(parts) != 3 or parts[0] != "tip":
        return None
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        return None
    if amount not in tip_presets():
        return None
    return user_id, amount


def pre_checkout_error(payload: str, *, payer_id: int, total_amount: int) -> str | None:
    """None — ok, иначе текст ошибки для pre_checkout."""
    if not tips_enabled():
        return "Stars временно недоступны"
    parsed = parse_tip_payload(payload)
    if parsed is None:
        return "Неизвестный платёж"
    user_id, amount = parsed
    if user_id != payer_id:
        return "Платёж привязан к другому пользователю"
    if total_amount != amount:
        return "Сумма не совпадает"
    return None


def tip_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for amount in tip_presets():
        row.append(
            InlineKeyboardButton(
                text=f"{amount} ⭐",
                callback_data=f"tip:pay:{amount}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_thanks_screen(*, subscribe_redirect: bool = False) -> str:
    presets = ", ".join(str(n) for n in tip_presets())
    lead = ""
    if subscribe_redirect:
        lead = (
            "ℹ️ Подписки Pro больше нет — бот бесплатный. "
            "Stars только как «спасибо» автору.\n\n"
        )
    return (
        f"{lead}"
        "⭐ <b>Благодарность автору</b>\n\n"
        "Все функции бесплатны. Stars — добровольная поддержка, "
        "если бот помогает в делах.\n\n"
        f"Выбери сумму: <b>{presets}</b> ⭐"
    )


def format_tips_disabled(*, from_subscribe: bool = False) -> str:
    extra = ""
    if from_subscribe:
        extra = "\n\n<i>/subscribe</i> больше не про подписку — лимитов нет."
    return (
        "⭐ Благодарность Stars пока недоступна.\n\n"
        "Все функции бота остаются бесплатными · /about"
        f"{extra}"
    )


def format_thank_you(amount: int, *, first_name: str | None = None) -> str:
    thanks = f"Спасибо, {first_name}!" if first_name else "Спасибо!"
    return (
        f"{thanks} ⭐ Ты отправил <b>{amount}</b> Stars — "
        "это правда приятно.\n\n"
        "Бот остаётся бесплатным для всех · /help"
    )


def format_thank_you_duplicate() -> str:
    return "✅ Спасибо! Этот платёж уже учтён."


def tip_invoice_prices(amount: int) -> list[LabeledPrice]:
    return [LabeledPrice(label="Благодарность автору", amount=amount)]
