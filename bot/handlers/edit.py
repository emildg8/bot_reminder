import re

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, get_reminder
from bot.keyboards.inline import confirm_reminder_keyboard, task_time_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_delivery import resolve_delivery_chat_id
from bot.services.chat_permissions import bot_can_post_reminders, format_bot_cannot_post_hint
from bot.services.collective_confirm import collective_dm_failed_suffix, send_collective_confirm
from bot.services.collective_preview import build_group_confirm_preview
from bot.services.drafts import clear_edit_pending, pop_edit_pending, set_edit_pending, store_draft
from bot.services.pending_tasks import store_pending_task
from bot.services.mention_create import extract_create_mention, mention_was_provided
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.ambiguous_prompt import offer_ambiguous_time_choice
from bot.services.nlp.llm_parser import parse_all_reminders
from bot.services.reminder_display import format_batch_parsed_summary_html, format_parsed_summary_html
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat
from bot.texts.messages import (
    format_confirm_card,
    format_mention_assignee_line,
    format_parse_fail,
    looks_like_task_only,
)

router = Router()

EDIT_CMD_PATTERN = re.compile(
    r"^/edit(?:@\w+)?(?:\s+#?(\d+)(?:\s+(.+))?)?$",
    re.DOTALL | re.IGNORECASE,
)


@router.message(lambda m: m.text and EDIT_CMD_PATTERN.match(m.text.strip()))
async def cmd_edit(message: Message, bot: Bot) -> None:
    match = EDIT_CMD_PATTERN.match(message.text.strip())
    reminder_id_str, new_phrase = match.group(1), match.group(2)

    if reminder_id_str is None:
        await message.answer(
            "Формат:\n"
            "<code>/edit 24</code> — затем новая фраза\n"
            "<code>/edit 24 через 2 часа новый текст</code>\n\n"
            "В группе кнопки ✏️ нет — только команды.\n"
            "В личке: ✏️ в /list",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    reminder_id = int(reminder_id_str)
    await _start_edit_flow(message, reminder_id, new_phrase, bot)


@router.callback_query(F.data.startswith("edit:"))
async def edit_button(callback: CallbackQuery, bot: Bot) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    await _start_edit_flow(
        callback.message, reminder_id, phrase=None, user_id=callback.from_user.id, bot=bot
    )
    await callback.answer()


async def _start_edit_flow(
    message: Message,
    reminder_id: int,
    phrase: str | None,
    bot: Bot,
    user_id: int | None = None,
) -> None:
    uid = user_id or message.from_user.id
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await message.answer("Напоминание не найдено.")
            return
        if reminder.created_by_telegram_id != uid:
            await message.answer("Можно редактировать только свои напоминания.")
            return
        user = await get_or_create_user(session, uid, settings.default_timezone)
        timezone = reminder.timezone or user.timezone

    if phrase:
        await _parse_and_confirm_edit(message, reminder_id, phrase, timezone, uid, bot)
        return

    set_edit_pending(uid, reminder_id)
    await message.answer(
        f"✏️ Редактирование #{reminder_id}.\n"
        "Отправь новую фразу, например:\n"
        "<code>через 1 час новый текст</code>\n"
        "<code>@user через 1 час задача</code>\n\n"
        "Отмена: /cancel",
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )


async def process_edit_phrase(message: Message, phrase: str, bot: Bot) -> bool:
    """Обрабатывает текст в режиме редактирования. Возвращает True если обработано."""
    reminder_id = pop_edit_pending(message.from_user.id)
    if reminder_id is None:
        return False

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await message.answer("Напоминание не найдено.")
            return True
        timezone = reminder.timezone

    await _parse_and_confirm_edit(message, reminder_id, phrase, timezone, message.from_user.id, bot)
    return True


async def _parse_and_confirm_edit(
    message: Message,
    reminder_id: int,
    phrase: str,
    timezone: str,
    user_id: int,
    bot: Bot,
) -> None:
    me = await bot.get_me()
    mention = extract_create_mention(
        message,
        phrase,
        bot_username=me.username,
        bot_id=me.id,
    )
    mention_telegram_id = await resolve_mention_user_id(
        bot, mention.user_id, mention.username, chat_id=message.chat.id
    )
    phrase_text = mention.phrase

    if await offer_ambiguous_time_choice(
        message, phrase_text, user_id, edit_reminder_id=reminder_id
    ):
        return

    parsed_items = await parse_all_reminders(phrase_text, timezone)
    if not parsed_items:
        set_edit_pending(user_id, reminder_id)
        kind = chat_kind_from_chat(message.chat)
        fail_kwargs = {"chat_kind": kind, "bot_username": me.username}
        if looks_like_task_only(phrase_text):
            store_pending_task(user_id, phrase_text, edit_reminder_id=reminder_id)
            await message.answer(
                format_parse_fail(phrase_text, **fail_kwargs),
                reply_markup=task_time_keyboard(),
            )
        else:
            await message.answer(
                format_parse_fail(phrase_text, **fail_kwargs),
                reply_markup=menu_keyboard_for_chat(message.chat.id),
            )
        return

    clear_edit_pending(user_id)
    async with async_session() as session:
        delivery_chat_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )
    summary = (
        format_batch_parsed_summary_html(parsed_items, timezone)
        if len(parsed_items) > 1
        else format_parsed_summary_html(parsed_items[0], timezone)
    )
    prefix = format_mention_assignee_line(
        mention_telegram_id,
        mention.username,
        resolved=mention_telegram_id is not None or not mention.username,
        source=mention.source,
        pick_note=mention.pick_note,
    )

    if chat_kind_from_chat(message.chat) != ChatKind.PRIVATE:
        if delivery_chat_id != message.chat.id:
            prefix += "📢 Публикация — в <b>канале</b> (из группы обсуждений).\n\n"
        if not await bot_can_post_reminders(bot, delivery_chat_id):
            prefix += format_bot_cannot_post_hint() + "\n\n"

    mention_provided = mention_was_provided(mention)
    chat_kind = chat_kind_from_chat(message.chat)
    draft_id = store_draft(
        user_id,
        parsed_items=parsed_items,
        mention_telegram_id=mention_telegram_id,
        mention_username=mention.username,
        mention_source=mention.source,
        mention_provided=mention_provided,
        edit_reminder_id=reminder_id,
        collective_chat_id=message.chat.id if chat_kind != ChatKind.PRIVATE else None,
        collective_chat_kind=chat_kind if chat_kind != ChatKind.PRIVATE else None,
        delivery_chat_id=delivery_chat_id if chat_kind != ChatKind.PRIVATE else None,
    )
    if chat_kind != ChatKind.PRIVATE:
        body = prefix + summary
    else:
        body = format_confirm_card(summary, is_edit=True)
        if len(parsed_items) > 1:
            body = body.replace("Подтверди действие:", "Подтверди замену:")
        if prefix:
            body = prefix + body

    mention_resolved = mention_telegram_id is not None or not mention.username
    if chat_kind != ChatKind.PRIVATE:
        group_preview = build_group_confirm_preview(
            parsed_items,
            timezone,
            mention_username=mention.username,
            mention_source=mention.source,
            mention_resolved=mention_resolved,
        )
        sent_dm = await send_collective_confirm(
            bot,
            user_id=user_id,
            collective_chat_id=message.chat.id,
            collective_kind=chat_kind,
            chat_title=message.chat.title,
            body=body,
            reply_markup=confirm_reminder_keyboard(draft_id, edit_id=reminder_id),
            group_preview=group_preview,
        )
        if not sent_dm:
            me = await bot.get_me()
            await message.answer(
                body + collective_dm_failed_suffix(me.username),
                reply_markup=confirm_reminder_keyboard(draft_id, edit_id=reminder_id),
            )
        return

    await message.answer(
        body,
        reply_markup=confirm_reminder_keyboard(draft_id, edit_id=reminder_id),
    )
