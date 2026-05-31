from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from zoneinfo import ZoneInfo

from bot.config import settings
from bot.db.models import ReminderEventKind
from bot.db.repository import (
    async_session,
    deactivate_reminder,
    get_or_create_user,
    get_reminder,
    get_user_by_telegram_id,
    update_reminder_next_run,
)
from bot.keyboards.inline import (
    delete_confirm_keyboard,
    duplicate_confirm_keyboard,
    reminder_actions_keyboard,
    snooze_picker_keyboard,
)
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.drafts import DraftEntry, discard_draft, pop_draft, store_draft
from bot.services.duplicates import find_duplicate_reminder
from bot.services.reminder_create import create_and_schedule_items
from bot.services.reminder_history import log_reminder_event
from bot.services.reminder_apply import apply_parsed_to_reminder
from bot.services.snooze_picker import clear_picker, get_picker, set_picker
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat
from bot.services.chat_permissions import bot_can_post_reminders, format_bot_cannot_post_hint
from bot.services.collective_confirm import send_collective_duplicate_confirm
from bot.services.timezone_ctx import get_effective_timezone
from bot.services.user_prefs import (
    clamp_snooze_minutes,
    format_snooze_minutes,
    get_default_snooze_minutes,
    get_snooze_presets,
    get_snooze_step,
)
from bot.texts.messages import (
    format_batch_created,
    format_collective_batch_notice,
    format_collective_created_notice,
    format_created,
    format_edit_replaced,
    format_group_reminder_hint,
    format_updated,
)
from bot.services.reminder_display import format_parsed_when_label
from bot.services.channel_schedule import (
    cancel_reminder_telegram_schedule,
    setup_channel_telegram_schedule,
)
from bot.services.reminder_jobs import cancel_reminder_job, teardown_reminder_schedule
from bot.services.scheduler import schedule_reminder, scheduler

router = Router()


def _draft_target(entry: DraftEntry, callback: CallbackQuery) -> tuple[int, ChatKind | None]:
    delivery = entry.delivery_chat_id or entry.collective_chat_id
    if delivery is not None:
        kind = entry.collective_chat_kind
        return delivery, kind
    kind = chat_kind_from_chat(callback.message.chat)
    collective = kind if kind != ChatKind.PRIVATE else None
    return callback.message.chat.id, collective


async def _reply_after_create(
    callback: CallbackQuery,
    bot: Bot,
    created: list[tuple[int, str, str]],
    *,
    entry: DraftEntry | None = None,
) -> None:
    target_chat_id, collective = _draft_target(entry, callback) if entry else (
        callback.message.chat.id,
        chat_kind_from_chat(callback.message.chat)
        if chat_kind_from_chat(callback.message.chat) != ChatKind.PRIVATE
        else None,
    )
    if collective is None and entry and entry.collective_chat_kind:
        collective = entry.collective_chat_kind

    if len(created) == 1:
        rid, when, text = created[0]
        await callback.message.edit_text(format_created(rid, when, text, collective=collective))
    else:
        await callback.message.edit_text(format_batch_created(created, collective=collective))

    if collective is not None and entry and entry.collective_chat_id:
        user = callback.from_user
        if len(created) == 1:
            rid, when, text = created[0]
            notice = format_collective_created_notice(
                creator_username=user.username,
                creator_user_id=user.id,
                reminder_id=rid,
                when=when,
                text=text,
                chat_kind=collective,
            )
        else:
            notice = format_collective_batch_notice(
                creator_username=user.username,
                creator_user_id=user.id,
                count=len(created),
                chat_kind=collective,
            )
        try:
            await bot.send_message(entry.collective_chat_id, notice)
        except Exception:
            pass
        me = await bot.get_me()
        if not await bot_can_post_reminders(bot, target_chat_id):
            try:
                await bot.send_message(entry.collective_chat_id, format_bot_cannot_post_hint())
            except Exception:
                pass
        try:
            await bot.send_message(
                callback.from_user.id,
                format_group_reminder_hint(me.username),
            )
        except Exception:
            pass
    elif collective is not None:
        me = await bot.get_me()
        await callback.message.answer(format_group_reminder_hint(me.username))
        if not await bot_can_post_reminders(bot, target_chat_id):
            await callback.message.answer(format_bot_cannot_post_hint())
    elif kb := menu_keyboard_for_chat(callback.message.chat.id):
        await callback.message.answer("Меню:", reply_markup=kb)
    await callback.answer()


async def _create_from_draft(
    callback: CallbackQuery,
    bot: Bot,
    draft_id: str,
    *,
    skip_duplicate: bool = False,
) -> None:
    entry = pop_draft(draft_id, callback.from_user.id)
    if entry is None:
        await callback.answer("Черновик не найден или устарел.", show_alert=True)
        return

    batch = len(entry.parsed_items) > 1
    check_duplicate = not skip_duplicate and not batch
    target_chat_id, collective_kind = _draft_target(entry, callback)

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone=settings.default_timezone,
        )
        tz = await get_effective_timezone(
            session, target_chat_id, callback.from_user.id
        )

        if check_duplicate:
            duplicate = await find_duplicate_reminder(
                session,
                target_chat_id,
                entry.parsed.text,
                entry.parsed.kind,
                parsed=entry.parsed,
                timezone=tz,
                created_by=callback.from_user.id,
            )
            if duplicate:
                new_draft_id = store_draft(
                    callback.from_user.id,
                    parsed_items=entry.parsed_items,
                    mention_telegram_id=entry.mention_telegram_id,
                    mention_provided=entry.mention_provided,
                    collective_chat_id=entry.collective_chat_id,
                    collective_chat_kind=entry.collective_chat_kind,
                    delivery_chat_id=entry.delivery_chat_id,
                )
                dup_body = (
                    f"⚠️ Похожее напоминание уже есть (#{duplicate.id}).\n"
                    f"📝 {entry.parsed.text}"
                )
                dup_kb = duplicate_confirm_keyboard(new_draft_id, duplicate.id)
                if entry.collective_chat_id and collective_kind:
                    sent = await send_collective_duplicate_confirm(
                        bot,
                        user_id=callback.from_user.id,
                        collective_chat_id=entry.collective_chat_id,
                        collective_kind=collective_kind,
                        chat_title=None,
                        body=dup_body,
                        reply_markup=dup_kb,
                    )
                    if sent:
                        await callback.message.edit_text("⚠️ Дубликат — подтверди в сообщении выше.")
                    else:
                        await callback.message.edit_text(dup_body, reply_markup=dup_kb)
                else:
                    await callback.message.edit_text(dup_body, reply_markup=dup_kb)
                await callback.answer()
                return

        created = await create_and_schedule_items(
            session,
            bot,
            user_id=user.id,
            chat_id=target_chat_id,
            created_by_telegram_id=callback.from_user.id,
            timezone=tz,
            parsed_items=entry.parsed_items,
            mention_telegram_id=entry.mention_telegram_id,
        )

    await _reply_after_create(callback, bot, created, entry=entry)


@router.callback_query(lambda c: c.data and c.data.startswith("confirm:"))
async def confirm_reminder(callback: CallbackQuery, bot: Bot) -> None:
    draft_id = callback.data.split(":", 1)[1]
    await _create_from_draft(callback, bot, draft_id)


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_force:"))
async def confirm_force_reminder(callback: CallbackQuery, bot: Bot) -> None:
    draft_id = callback.data.split(":", 1)[1]
    await _create_from_draft(callback, bot, draft_id, skip_duplicate=True)


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_edit:"))
async def confirm_edit_reminder(callback: CallbackQuery, bot: Bot) -> None:
    _, reminder_id_str, draft_id = callback.data.split(":", 2)
    reminder_id = int(reminder_id_str)

    entry = pop_draft(draft_id, callback.from_user.id)
    if entry is None:
        await callback.answer("Черновик не найден или устарел.", show_alert=True)
        return

    target_chat_id, collective = _draft_target(entry, callback)

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone=settings.default_timezone,
        )
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return
        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        tz = reminder.timezone or user.timezone
        cancel_reminder_job(reminder_id)

        if len(entry.parsed_items) == 1:
            next_run = await apply_parsed_to_reminder(
                session, reminder, entry.parsed, tz
            )
            if entry.mention_provided:
                reminder.mention_telegram_id = entry.mention_telegram_id
                await session.commit()
            schedule_reminder(bot, reminder_id, next_run, timezone=tz)
            refreshed = await get_reminder(session, reminder_id)
            if refreshed is not None:
                await setup_channel_telegram_schedule(bot, session, refreshed)
            when = format_parsed_when_label(entry.parsed, tz)
            await callback.message.edit_text(format_updated(reminder_id, when))
        else:
            await teardown_reminder_schedule(bot, session, reminder)
            await deactivate_reminder(session, reminder)
            created = await create_and_schedule_items(
                session,
                bot,
                user_id=user.id,
                chat_id=target_chat_id,
                created_by_telegram_id=callback.from_user.id,
                timezone=tz,
                parsed_items=entry.parsed_items,
                mention_telegram_id=entry.mention_telegram_id,
            )
            await callback.message.edit_text(
                format_edit_replaced(reminder_id, created, collective=collective)
            )

    if entry.collective_chat_id and collective is not None and len(entry.parsed_items) > 1:
        me = await bot.get_me()
        try:
            await bot.send_message(callback.from_user.id, format_group_reminder_hint(me.username))
        except Exception:
            pass
        try:
            await bot.send_message(
                entry.collective_chat_id,
                format_collective_batch_notice(
                    creator_username=callback.from_user.username,
                    creator_user_id=callback.from_user.id,
                    count=len(entry.parsed_items),
                    chat_kind=collective,
                ),
            )
        except Exception:
            pass
    elif kb := menu_keyboard_for_chat(callback.message.chat.id):
        await callback.message.answer("Меню:", reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("cancel:"))
async def cancel_draft(callback: CallbackQuery) -> None:
    draft_id = callback.data.split(":", 1)[1]
    discard_draft(draft_id, callback.from_user.id)
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("snooze:"))
async def snooze_reminder_legacy(callback: CallbackQuery, bot: Bot) -> None:
    """Старые сообщения с +5/+15/+30."""
    _, reminder_id_str, minutes_str = callback.data.split(":")
    await _apply_snooze(callback, bot, int(reminder_id_str), int(minutes_str))


@router.callback_query(lambda c: c.data and c.data.startswith("szm:"))
async def snooze_menu(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return
        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        default_mins = get_default_snooze_minutes(user)
        presets = get_snooze_presets(user)

    set_picker(callback.from_user.id, reminder_id, default_mins)
    await callback.message.edit_text(
        f"⏰ <b>Отложить</b>\n📝 {reminder.text}\n\n"
        "Выбери быстрый вариант или измени время кнопками − / +:",
        reply_markup=snooze_picker_keyboard(reminder_id, default_mins, presets),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("szs:"))
async def snooze_set_preset(callback: CallbackQuery) -> None:
    _, reminder_id_str, minutes_str = callback.data.split(":")
    reminder_id = int(reminder_id_str)
    minutes = clamp_snooze_minutes(int(minutes_str))
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        presets = get_snooze_presets(user)
    set_picker(callback.from_user.id, reminder_id, minutes)
    await callback.message.edit_reply_markup(
        reply_markup=snooze_picker_keyboard(reminder_id, minutes, presets),
    )
    await callback.answer(format_snooze_minutes(minutes))


@router.callback_query(lambda c: c.data and c.data.startswith("sz+:"))
async def snooze_inc(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        step = get_snooze_step(user)
        presets = get_snooze_presets(user)
    state = get_picker(callback.from_user.id, reminder_id)
    current = state.minutes if state else get_default_snooze_minutes(user)
    minutes = clamp_snooze_minutes(current + step)
    set_picker(callback.from_user.id, reminder_id, minutes)
    await callback.message.edit_reply_markup(
        reply_markup=snooze_picker_keyboard(reminder_id, minutes, presets),
    )
    await callback.answer(format_snooze_minutes(minutes))


@router.callback_query(lambda c: c.data and c.data.startswith("sz-:"))
async def snooze_dec(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        step = get_snooze_step(user)
        presets = get_snooze_presets(user)
    state = get_picker(callback.from_user.id, reminder_id)
    current = state.minutes if state else get_default_snooze_minutes(user)
    minutes = clamp_snooze_minutes(current - step)
    set_picker(callback.from_user.id, reminder_id, minutes)
    await callback.message.edit_reply_markup(
        reply_markup=snooze_picker_keyboard(reminder_id, minutes, presets),
    )
    await callback.answer(format_snooze_minutes(minutes))


@router.callback_query(F.data == "sznoop")
async def snooze_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("sza:"))
async def snooze_apply(callback: CallbackQuery, bot: Bot) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    state = get_picker(callback.from_user.id, reminder_id)
    if state is None:
        await callback.answer("Выбери время заново.", show_alert=True)
        return
    await _apply_snooze(callback, bot, reminder_id, state.minutes)
    clear_picker(callback.from_user.id)


@router.callback_query(lambda c: c.data and c.data.startswith("szb:"))
async def snooze_back(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    clear_picker(callback.from_user.id)
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
    if reminder is None:
        await callback.answer("Напоминание не найдено.", show_alert=True)
        return
    from bot.services.telegram_format import format_reminder_message

    body = format_reminder_message(reminder.text, chat_id=reminder.chat_id)
    await callback.message.edit_text(
        body,
        reply_markup=reminder_actions_keyboard(reminder_id),
    )
    await callback.answer()


async def _apply_snooze(callback: CallbackQuery, bot: Bot, reminder_id: int, minutes: int) -> None:
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        if not reminder.is_active:
            if reminder.kind != "once":
                await callback.answer("Напоминание не найдено.", show_alert=True)
                return
            reminder.is_active = True
            await session.commit()
            await session.refresh(reminder)

        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        tz = ZoneInfo(reminder.timezone)
        next_run = datetime.now(tz) + timedelta(minutes=minutes)
        await cancel_reminder_telegram_schedule(bot, session, reminder)
        await update_reminder_next_run(session, reminder, next_run)
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=reminder.chat_id,
            user_telegram_id=callback.from_user.id,
            text=reminder.text,
            kind=ReminderEventKind.SNOOZED,
            extra={"minutes": minutes},
        )

    cancel_reminder_job(reminder_id)
    schedule_reminder(bot, reminder_id, next_run, timezone=reminder.timezone)
    async with async_session() as session:
        refreshed = await get_reminder(session, reminder_id)
        if refreshed is not None:
            await setup_channel_telegram_schedule(bot, session, refreshed)
    when = next_run.strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(
        f"⏰ Отложено на <b>{format_snooze_minutes(minutes)}</b> (до {when})\n"
        f"📝 {reminder.text}",
        reply_markup=reminder_actions_keyboard(reminder_id),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("done:"))
async def done_reminder(callback: CallbackQuery, bot: Bot) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        await teardown_reminder_schedule(bot, session, reminder)
        await deactivate_reminder(session, reminder)
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=reminder.chat_id,
            user_telegram_id=callback.from_user.id,
            text=reminder.text,
            kind=ReminderEventKind.DONE,
        )

    await callback.message.edit_text("✅ Готово. Напоминание закрыто.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("del_confirm:"))
async def delete_confirm(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return
        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

    await callback.message.edit_text(
        f"🗑 Удалить напоминание #{reminder_id}?\n📝 {reminder.text}",
        reply_markup=delete_confirm_keyboard(reminder_id),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("del_cancel:"))
async def delete_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Отменено.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 К списку", callback_data="menu:list")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("delete:"))
async def delete_reminder(callback: CallbackQuery, bot: Bot) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        await teardown_reminder_schedule(bot, session, reminder)
        await deactivate_reminder(session, reminder)
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=reminder.chat_id,
            user_telegram_id=callback.from_user.id,
            text=reminder.text,
            kind=ReminderEventKind.DELETED,
        )

    await callback.message.edit_text("🗑 Напоминание удалено.")
    await callback.answer()
