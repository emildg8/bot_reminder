"""Добровольная благодарность автору через Telegram Stars."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import User
from bot.db.repository import count_user_done_reminders, count_user_star_tips, get_user_by_telegram_id

_TIP_TOKENS = ("⭐", "stars", "star", "xtr", "звёзд", "звезд", "звезда", "звезды")
_LETTERS_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ]")
_REMINDER_HINTS = re.compile(
    r"(?:завтра|сегодня|послезавтра|через|кажд|минут|мин\.?|час|ч\.?|"
    r"недел|месяц|утром|вечером|ночью|"
    r"пн|вт|ср|чт|пт|сб|вс|"
    r"remind|tomorrow|today|every|minute|hour)",
    re.IGNORECASE,
)


def tips_enabled() -> bool:
    return settings.stars_tips_enabled


def tip_presets() -> list[int]:
    return settings.stars_tip_preset_list()


def tip_amount_bounds() -> tuple[int, int]:
    return settings.stars_tip_min, settings.stars_tip_max


def text_has_letters(text: str) -> bool:
    return bool(_LETTERS_RE.search(text or ""))


def looks_like_reminder_phrase(text: str) -> bool:
    """Фраза напоминания — не перехватывать в режиме «своя сумма»."""
    raw = (text or "").strip()
    if not text_has_letters(raw):
        return False
    if len(raw.split()) >= 2:
        return True
    return bool(_REMINDER_HINTS.search(raw))


def parse_tip_amount_input(text: str) -> int | None:
    """Из «75», «75 ⭐», «1 000 stars» → int или None."""
    raw = (text or "").strip().lower()
    for token in _TIP_TOKENS:
        raw = raw.replace(token, "")
    raw = raw.replace(" ", "").replace("\u00a0", "").replace(",", "")
    if not raw.isdigit():
        return None
    return int(raw)


def looks_like_tip_amount(text: str) -> bool:
    if parse_tip_amount_input(text) is not None:
        return True
    raw = (text or "").strip().lower()
    for token in _TIP_TOKENS:
        raw = raw.replace(token, "")
    raw = raw.replace(" ", "").replace("\u00a0", "").replace(",", "")
    return bool(raw) and raw.isdigit()


def _tip_times_word(count: int) -> str:
    if count % 100 in (11, 12, 13, 14):
        return "раз"
    last = count % 10
    if last == 1:
        return "раз"
    if last in (2, 3, 4):
        return "раза"
    return "раз"


def is_valid_tip_amount(amount: int) -> bool:
    lo, hi = tip_amount_bounds()
    return lo <= amount <= hi


def user_had_pro(user: User) -> bool:
    return bool(user.is_pro or user.pro_expires_at is not None)


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
    if not is_valid_tip_amount(amount):
        return None
    return user_id, amount


def is_tip_payload(payload: str) -> bool:
    return (payload or "").startswith("tip:")


def pre_checkout_error(payload: str, *, payer_id: int, total_amount: int) -> str | None:
    """None — ok, иначе текст ошибки для pre_checkout (только tip:*)."""
    if not is_tip_payload(payload):
        return None
    parsed = parse_tip_payload(payload)
    if parsed is None:
        return "Неизвестный платёж"
    user_id, amount = parsed
    if user_id != payer_id:
        return "Платёж привязан к другому пользователю"
    if total_amount != amount:
        return "Сумма не совпадает"
    return None


def _preset_button_label(amount: int) -> str:
    if amount <= 50:
        return f"☕ {amount} ⭐"
    if amount <= 250:
        return f"🙏 {amount} ⭐"
    return f"💫 {amount} ⭐"


def tip_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for amount in tip_presets():
        row.append(
            InlineKeyboardButton(
                text=_preset_button_label(amount),
                callback_data=f"tip:pay:{amount}",
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(text="✨ Другая сумма", callback_data="tip:custom")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def custom_amount_confirm_keyboard(amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Отправить {amount} ⭐",
                    callback_data=f"tip:confirm:{amount}",
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="tip:back")],
        ]
    )


def custom_amount_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К суммам", callback_data="tip:back")],
        ]
    )


def tip_thank_you_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Автор", callback_data="menu:author"),
                InlineKeyboardButton(text="⭐ Ещё раз", callback_data="menu:thanks"),
            ],
        ]
    )


def tip_nudge_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Поддержать", callback_data="menu:thanks")],
            [InlineKeyboardButton(text="Не сейчас", callback_data="tip:nudge:dismiss")],
        ]
    )


def _nudge_cooldown_elapsed(at: datetime | None) -> bool:
    if at is None:
        return True
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - at).total_seconds()
    return elapsed >= max(1, settings.stars_tip_nudge_days) * 86400


async def should_send_tip_nudge(session: AsyncSession, user_id: int) -> bool:
    if not tips_enabled() or not settings.stars_tip_nudge_enabled:
        return False
    user = await get_user_by_telegram_id(session, user_id)
    if user is None:
        return False
    tip_count, _ = await count_user_star_tips(session, user_id)
    if tip_count > 0:
        return False
    if settings.stars_tip_nudge_once:
        if user.tip_nudge_at is not None:
            return False
    else:
        anchor = user.tip_nudge_dismissed_at or user.tip_nudge_at
        if anchor is not None and not _nudge_cooldown_elapsed(anchor):
            return False
    min_dones = settings.stars_tip_nudge_min_dones
    if min_dones > 0:
        dones = await count_user_done_reminders(session, user_id)
        if dones < min_dones:
            return False
    return True


def format_tip_nudge() -> str:
    return (
        "💡 Бот бесплатный. Если помог — можно "
        "отблагодарить автора Stars, это необязательно."
    )


def format_prior_tips_line(count: int, total: int) -> str:
    return f"Ты уже поддержал: <b>{total}</b> ⭐ ({count} {_tip_times_word(count)})\n\n"


def format_thanks_screen(
    *,
    subscribe_redirect: bool = False,
    prior_tips: tuple[int, int] | None = None,
) -> str:
    lo, hi = tip_amount_bounds()
    lead = ""
    if subscribe_redirect:
        lead = (
            "ℹ️ Подписки Pro больше нет — бот бесплатный. "
            "Stars только как «спасибо» автору.\n\n"
        )
    history = ""
    if prior_tips:
        count, total = prior_tips
        if count > 0:
            history = format_prior_tips_line(count, total)
    return (
        f"{lead}"
        "⭐ <b>Благодарность автору</b>\n\n"
        "Бот полностью бесплатный — Stars только как «спасибо», "
        "если напоминания реально выручают.\n\n"
        f"{history}"
        f"Выбери сумму кнопкой ниже или свою — от <b>{lo}</b> до <b>{hi}</b> ⭐"
    )


def format_custom_amount_prompt() -> str:
    lo, hi = tip_amount_bounds()
    return (
        f"✨ <b>Своя сумма</b>\n\n"
        f"Напиши число от <b>{lo}</b> до <b>{hi}</b> ⭐ "
        f"(можно «75» или «75 ⭐»).\n"
        "Фраза напоминания («завтра созвон») — выйдет из режима суммы.\n"
        "/cancel — отмена."
    )


def format_custom_amount_confirm(amount: int) -> str:
    return (
        f"Отправить <b>{amount}</b> ⭐ автору?\n\n"
        "Это добровольная благодарность — функции бота не меняются."
    )


def format_custom_amount_pending_hint() -> str:
    return "Подтверди кнопкой ↑ или отмени: /cancel"


def format_custom_amount_invalid(text: str) -> str:
    lo, hi = tip_amount_bounds()
    shown = (text or "").strip()[:40]
    return (
        f"Не понял: «{shown}».\n"
        f"Нужно целое число от {lo} до {hi} ⭐.\n"
        "Или напиши фразу напоминания — тогда режим суммы сбросится."
    )


def format_amount_out_of_range(amount: int) -> str:
    lo, hi = tip_amount_bounds()
    return f"Сумма <b>{amount}</b> вне диапазона — от {lo} до {hi} ⭐."


def format_start_bot_for_tips() -> str:
    return (
        "⚠️ Не могу написать в личку — сначала открой чат с ботом и нажми "
        "<b>/start</b>, затем снова <code>/thanks</code>."
    )


def format_invoice_sent(amount: int, *, sent_to_dm: bool = False) -> str:
    if sent_to_dm:
        return f"💫 Счёт на <b>{amount}</b> ⭐ отправлен в личку."
    return f"💫 Счёт на <b>{amount}</b> ⭐ — оплати в окне Telegram."


def format_tips_disabled(*, from_subscribe: bool = False) -> str:
    extra = ""
    if from_subscribe:
        extra = "\n\n<i>/subscribe</i> больше не про подписку — лимитов нет."
    return (
        "⭐ Благодарность Stars пока недоступна.\n\n"
        "Все функции бота остаются бесплатными · /about"
        f"{extra}"
    )


def format_thank_you(
    amount: int,
    *,
    first_name: str | None = None,
    total_tips: int | None = None,
) -> str:
    thanks = f"Спасибо, {first_name}!" if first_name else "Спасибо!"
    lines = [
        f"{thanks} ⭐ Ты отправил <b>{amount}</b> Stars — это правда приятно.",
    ]
    if total_tips is not None and total_tips > amount:
        lines.append(f"Всего поддержал: <b>{total_tips}</b> ⭐.")
    elif total_tips is not None and total_tips == amount:
        lines.append("Первый раз — очень приятно!")
    lines.append("")
    lines.append("Бот остаётся бесплатным для всех · /help")
    lines.append("Вопросы и идеи — /author")
    from bot.texts.messages import format_developer_contact_line

    lines.append(format_developer_contact_line())
    return "\n".join(lines)


def format_thank_you_duplicate() -> str:
    return "✅ Спасибо! Этот платёж уже учтён."


def tip_invoice_prices(amount: int) -> list[LabeledPrice]:
    return [LabeledPrice(label="Благодарность автору", amount=amount)]


async def send_tip_invoice(bot, *, chat_id: int, user_id: int, amount: int) -> None:
    await bot.send_invoice(
        chat_id=chat_id,
        title="Благодарность автору",
        description=f"Добровольная поддержка · {amount} ⭐",
        payload=tip_payload(user_id, amount),
        provider_token="",
        currency="XTR",
        prices=tip_invoice_prices(amount),
    )


async def deliver_tip_invoice(
    bot,
    *,
    user_id: int,
    amount: int,
    reply_chat_id: int,
) -> bool:
    """Invoice всегда в личку; подтверждение — в reply_chat_id. False — не удалось."""
    try:
        await send_tip_invoice(bot, chat_id=user_id, user_id=user_id, amount=amount)
    except TelegramBadRequest:
        await bot.send_message(reply_chat_id, format_start_bot_for_tips())
        return False
    sent_to_dm = reply_chat_id != user_id
    await bot.send_message(reply_chat_id, format_invoice_sent(amount, sent_to_dm=sent_to_dm))
    return True
