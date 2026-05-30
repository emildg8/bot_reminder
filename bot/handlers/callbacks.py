from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from zoneinfo import ZoneInfo

from bot.config import settings
from bot.db.models import ReminderEventKind
from bot.db.repository import (
    async_session,
    create_reminder,
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
from bot.keyboards.reply import main_menu_keyboard
from bot.services.drafts import discard_draft, pop_draft, store_draft
from bot.services.duplicates import find_duplicate_reminder
from bot.services.reminder_history import log_reminder_event
from bot.services.reminder_apply import apply_parsed_to_reminder
from bot.services.reminder_utils import compute_next_run, weekdays_to_mask
from bot.services.snooze_picker import clear_picker, get_picker, set_picker
from bot.services.user_prefs import (
    clamp_snooze_minutes,
    format_snooze_minutes,
    get_default_snooze_minutes,
    get_snooze_presets,
    get_snooze_step,
)
from bot.texts.messages import format_batch_created, format_created, format_updated
from bot.services.scheduler import schedule_reminder, scheduler
from bot.services.timezone_ctx import get_effective_timezone

router = Router()


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

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone=settings.default_timezone,
        )
        tz = await get_effective_timezone(
            session, callback.message.chat.id, callback.from_user.id
        )

        if check_duplicate:
            duplicate = await find_duplicate_reminder(
                session,
                callback.message.chat.id,
                entry.parsed.text,
                entry.parsed.kind,
                created_by=callback.from_user.id,
            )
            if duplicate:
                new_draft_id = store_draft(
                    callback.from_user.id,
                    parsed_items=entry.parsed_items,
                    mention_telegram_id=entry.mention_telegram_id,
                    mention_provided=entry.mention_provided,
                )
                await callback.message.edit_text(
                    f"⚠️ Похожее напоминание уже есть (#{duplicate.id}).\n"
                    f"📝 {entry.parsed.text}",
                    reply_markup=duplicate_confirm_keyboard(new_draft_id, duplicate.id),
                )
                await callback.answer()
                return

        created: list[tuple[int, str, str]] = []
        for parsed in entry.parsed_items:
            next_run = compute_next_run(parsed, tz)
            reminder = await create_reminder(
                session,
                user_id=user.id,
                chat_id=callback.message.chat.id,
                created_by_telegram_id=callback.from_user.id,
                timezone=tz,
                text=parsed.text,
                kind=parsed.kind,
                next_run_at=next_run,
                interval_seconds=parsed.interval_seconds,
                daily_time=parsed.daily_time,
                weekdays_mask=weekdays_to_mask(parsed.weekdays) if parsed.weekdays else None,
                mention_telegram_id=entry.mention_telegram_id,
            )
            await log_reminder_event(
                session,
                reminder=reminder,
                chat_id=callback.message.chat.id,
                user_telegram_id=callback.from_user.id,
                text=parsed.text,
                kind=ReminderEventKind.CREATED,
            )
            schedule_reminder(bot, reminder.id, next_run)
            when = next_run.astimezone(ZoneInfo(tz)).strftime("%d.%m.%Y %H:%M")
            created.append((reminder.id, when, parsed.text))

    if len(created) == 1:
        rid, when, text = created[0]
        await callback.message.edit_text(format_created(rid, when, text))
    else:
        await callback.message.edit_text(format_batch_created(created))
    await callback.message.answer("Меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


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

        job_id = f"reminder_{reminder_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        next_run = await apply_parsed_to_reminder(
            session, reminder, entry.parsed, reminder.timezone or user.timezone
        )
        if entry.mention_provided:
            reminder.mention_telegram_id = entry.mention_telegram_id
            await session.commit()

    schedule_reminder(bot, reminder_id, next_run)
    when = next_run.astimezone(ZoneInfo(reminder.timezone)).strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(format_updated(reminder_id, when))
    await callback.message.answer("Меню:", reply_markup=main_menu_keyboard())
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

    schedule_reminder(bot, reminder_id, next_run)
    when = next_run.strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(
        f"⏰ Отложено на <b>{format_snooze_minutes(minutes)}</b> (до {when})\n"
        f"📝 {reminder.text}",
        reply_markup=reminder_actions_keyboard(reminder_id),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("done:"))
async def done_reminder(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        await deactivate_reminder(session, reminder)
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=reminder.chat_id,
            user_telegram_id=callback.from_user.id,
            text=reminder.text,
            kind=ReminderEventKind.DONE,
        )

    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

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
async def delete_reminder(callback: CallbackQuery) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        if reminder.created_by_telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        await deactivate_reminder(session, reminder)
        await log_reminder_event(
            session,
            reminder=reminder,
            chat_id=reminder.chat_id,
            user_telegram_id=callback.from_user.id,
            text=reminder.text,
            kind=ReminderEventKind.DELETED,
        )

    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    await callback.message.edit_text("🗑 Напоминание удалено.")
    await callback.answer()
