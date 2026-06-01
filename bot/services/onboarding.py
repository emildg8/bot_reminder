"""Guided onboarding после первого выбора часового пояса."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ONBOARDING_STEPS: list[str] = [
    (
        "🎯 <b>Шаг 1 из 3 — Создание</b>\n\n"
        "Напиши одной фразой <b>когда</b> и <b>что</b>:\n"
        "• <code>через час созвон</code>\n"
        "• <code>завтра в 14:00 обед</code>\n\n"
        "🎤 Или скажи голосом — «завтра в два часа дня созвон»\n"
        "Можно нажать «Попробовать пример» 👇"
    ),
    (
        "📋 <b>Шаг 2 из 3 — Список</b>\n\n"
        "Все активные напоминания — кнопка <b>📋 Список</b> или /list.\n\n"
        "Под каждым напоминанием:\n"
        "• ⏰ <b>Отложить</b> — перенести на потом\n"
        "• ✅ <b>Готово</b> — закрыть задачу"
    ),
    (
        "✏️ <b>Шаг 3 из 3 — Изменение</b>\n\n"
        "Изменить текст или время:\n"
        "• кнопка <b>✏️ Изменить</b> в списке\n"
        "• или <code>/edit N завтра в 10:00 новый текст</code>\n\n"
        "Готово! Можешь создавать напоминания ✨"
    ),
]

ONBOARDING_TRY_EXAMPLE_INDEX = 5  # «⏱ Через 30 мин»


def onboarding_step_text(step: int) -> str:
    idx = max(0, min(step - 1, len(ONBOARDING_STEPS) - 1))
    return ONBOARDING_STEPS[idx]


def onboarding_keyboard(step: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if step == 1:
        rows.append(
            [
                InlineKeyboardButton(text="🎯 Попробовать пример", callback_data="onb:try"),
                InlineKeyboardButton(text="Дальше →", callback_data="onb:next:2"),
            ]
        )
    elif step == 2:
        rows.append([InlineKeyboardButton(text="Дальше →", callback_data="onb:next:3")])
    else:
        rows.append([InlineKeyboardButton(text="✅ Начать пользоваться", callback_data="onb:done")])

    if step < 3:
        rows.append([InlineKeyboardButton(text="Пропустить тур", callback_data="onb:skip")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
