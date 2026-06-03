"""Отправка confirm-карточки после парса (create / выбор assignee)."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from bot.keyboards.inline import confirm_reminder_keyboard
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat
from bot.services.chat_permissions import bot_can_post_reminders, format_bot_cannot_post_hint
from bot.services.collective_confirm import collective_dm_failed_suffix, send_collective_confirm
from bot.services.collective_preview import build_group_confirm_preview
from bot.services.drafts import store_draft
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_display import format_batch_parsed_summary_html
from bot.texts.messages import (
    format_confirm_card,
    format_collective_check_dm,
    format_mention_assignee_line,
)


async def deliver_create_confirm(
    message: Message,
    bot: Bot,
    *,
    user_id: int,
    parsed_items: list[ParsedReminder],
    timezone: str,
    delivery_chat_id: int,
    mention_telegram_id: int | None,
    mention_username: str | None,
    mention_source: str | None,
    mention_provided: bool,
    mention_pick_note: str | None,
    source_label: str,
    heard_text: str,
    mention_resolved: bool = True,
) -> None:
    summary = format_batch_parsed_summary_html(parsed_items, timezone)
    if source_label == "voice":
        prefix = f"🎤 Распознано: {heard_text}\n\n"
    elif source_label == "video_note":
        prefix = f"🔵 Из кружочка: {heard_text}\n\n"
    else:
        prefix = ""
    mention_resolved = mention_telegram_id is not None or not mention_username
    prefix += format_mention_assignee_line(
        mention_telegram_id,
        mention_username,
        resolved=mention_resolved,
        source=mention_source,
        pick_note=mention_pick_note,
    )

    chat_kind = chat_kind_from_chat(message.chat)
    if chat_kind != ChatKind.PRIVATE:
        if delivery_chat_id != message.chat.id:
            prefix += "📢 Публикация — в <b>канале</b> (из группы обсуждений).\n\n"
        if not await bot_can_post_reminders(bot, delivery_chat_id):
            prefix += format_bot_cannot_post_hint() + "\n\n"

    draft_id = store_draft(
        user_id,
        parsed_items=parsed_items,
        mention_telegram_id=mention_telegram_id,
        mention_username=mention_username,
        mention_source=mention_source,
        mention_provided=mention_provided,
        collective_chat_id=message.chat.id if chat_kind != ChatKind.PRIVATE else None,
        collective_chat_kind=chat_kind if chat_kind != ChatKind.PRIVATE else None,
        delivery_chat_id=delivery_chat_id if chat_kind != ChatKind.PRIVATE else None,
    )

    body = format_confirm_card(summary) if chat_kind == ChatKind.PRIVATE else (prefix + summary)
    if chat_kind == ChatKind.PRIVATE and prefix:
        body = prefix + body

    if chat_kind != ChatKind.PRIVATE:
        me = await bot.get_me()
        group_preview = build_group_confirm_preview(
            parsed_items,
            timezone,
            mention_username=mention_username,
            mention_source=mention_source,
            mention_resolved=mention_resolved,
        )
        sent_dm, group_hint = await send_collective_confirm(
            bot,
            user_id=user_id,
            collective_chat_id=message.chat.id,
            collective_kind=chat_kind,
            chat_title=message.chat.title,
            body=body,
            reply_markup=confirm_reminder_keyboard(draft_id),
            group_preview=group_preview,
            reply_to_message_id=message.message_id,
        )
        if not sent_dm:
            await message.answer(
                body + collective_dm_failed_suffix(me.username),
                reply_markup=confirm_reminder_keyboard(draft_id),
            )
        elif not group_hint:
            await message.reply(
                format_collective_check_dm(chat_kind, message.chat.title, preview=group_preview)
            )
        return

    await message.answer(body, reply_markup=confirm_reminder_keyboard(draft_id))
