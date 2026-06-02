"""Уточнение assignee кнопками, если в фразе несколько @user без времени."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone as dt_timezone

from aiogram.types import Message

from bot.keyboards.inline import assignee_choice_keyboard
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat
from bot.services.collective_preview import build_assignee_choice_task_preview
from bot.services.mention_parse import _time_anchor_index
from bot.services.nlp.schemas import ParsedReminder
from bot.services.pending_assignee import PendingAssigneeCreate, store_pending_assignee
from bot.texts.messages import format_assignee_choice_prompt


def should_offer_assignee_choice(candidates: list[str], phrase: str) -> bool:
    """Несколько @user и нет якоря времени — автовыбор ненадёжен."""
    return len(candidates) >= 2 and _time_anchor_index(phrase) is None


async def offer_assignee_choice(
    message: Message,
    *,
    user_id: int,
    parsed_items: list[ParsedReminder],
    phrase: str,
    candidates: list[str],
    timezone: str,
    delivery_chat_id: int,
    source_label: str,
    heard_text: str,
) -> bool:
    if not should_offer_assignee_choice(candidates, phrase):
        return False

    chat_kind = chat_kind_from_chat(message.chat)
    store_pending_assignee(
        PendingAssigneeCreate(
            user_id=user_id,
            parsed_items=parsed_items,
            phrase=phrase,
            candidates=tuple(candidates[:6]),
            timezone=timezone,
            delivery_chat_id=delivery_chat_id,
            source_label=source_label,
            heard_text=heard_text,
            collective_chat_id=message.chat.id if chat_kind != ChatKind.PRIVATE else None,
            collective_chat_kind=chat_kind if chat_kind != ChatKind.PRIVATE else None,
            created_at=datetime.now(dt_timezone.utc),
        )
    )
    task_preview = build_assignee_choice_task_preview(parsed_items)
    await message.answer(
        format_assignee_choice_prompt(candidates, task_preview=task_preview),
        reply_markup=assignee_choice_keyboard(candidates),
    )
    return True
