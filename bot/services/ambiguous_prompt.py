"""Уточнение двусмысленного времени — общая логика create/edit."""

from __future__ import annotations

from aiogram.types import Message

from bot.keyboards.inline import ambiguous_day_only_keyboard, ambiguous_hour_keyboard
from bot.services.drafts import set_edit_pending
from bot.services.nlp.ambiguous_time import detect_ambiguous_day_hour, detect_ambiguous_day_only
from bot.services.pending_tasks import store_pending_task
from bot.texts.messages import format_ambiguous_day_prompt, format_ambiguous_hour_prompt


async def offer_ambiguous_time_choice(
    message: Message,
    phrase: str,
    user_id: int,
    *,
    edit_reminder_id: int | None = None,
) -> bool:
    """Сохраняет pending и показывает кнопки. True — фраза обработана."""
    ambiguous = detect_ambiguous_day_hour(phrase)
    if ambiguous:
        store_pending_task(
            user_id,
            ambiguous.task,
            ambiguous_day=ambiguous.day,
            ambiguous_hour=ambiguous.hour,
            edit_reminder_id=edit_reminder_id,
        )
        if edit_reminder_id is not None:
            set_edit_pending(user_id, edit_reminder_id)
        await message.answer(
            format_ambiguous_hour_prompt(ambiguous.task, ambiguous.day, ambiguous.hour),
            reply_markup=ambiguous_hour_keyboard(),
        )
        return True

    day_only = detect_ambiguous_day_only(phrase)
    if day_only:
        store_pending_task(
            user_id,
            day_only.task,
            ambiguous_day=day_only.day,
            edit_reminder_id=edit_reminder_id,
        )
        if edit_reminder_id is not None:
            set_edit_pending(user_id, edit_reminder_id)
        await message.answer(
            format_ambiguous_day_prompt(day_only.task, day_only.day),
            reply_markup=ambiguous_day_only_keyboard(),
        )
        return True

    return False
