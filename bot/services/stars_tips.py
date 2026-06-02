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


def tip_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for amount in tip_presets():
        row.append(
            InlineKeyboardButton(
                text=f"⭐ {amount}",
                callback_data=f"tip:pay:{amount}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_thanks_screen() -> str:
    presets = ", ".join(str(n) for n in tip_presets())
    return (
        "⭐ <b>Благодарность автору</b>\n\n"
        "Бот бесплатный для всех. Stars — добровольная поддержка, "
        "если хочешь сказать «спасибо» разработчику.\n\n"
        f"Выбери сумму ({presets} ⭐) или нажми кнопку ниже."
    )


def format_tips_disabled() -> str:
    return (
        "⭐ Благодарность Stars пока недоступна.\n\n"
        "Все функции бота остаются бесплатными · /about"
    )


def format_thank_you(amount: int) -> str:
    return (
        f"Спасибо! ⭐ Ты отправил <b>{amount}</b> Stars — "
        "это правда приятно.\n\n"
        "Бот остаётся бесплатным для всех · /help"
    )


def format_thank_you_duplicate() -> str:
    return "✅ Спасибо! Этот платёж уже учтён."


def tip_invoice_prices(amount: int) -> list[LabeledPrice]:
    return [LabeledPrice(label="Благодарность автору", amount=amount)]
