from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from zoneinfo import ZoneInfo

from bot.config import settings
from bot.db.repository import (
    async_session,
    create_reminder,
    deactivate_reminder,
    get_or_create_user,
    get_reminder,
    update_reminder_next_run,
)
from bot.keyboards.reply import main_menu_keyboard
from bot.services.drafts import discard_draft, pop_draft
from bot.services.duplicates import find_duplicate_reminder
from bot.texts.messages import format_confirm_card, format_created, format_updated
from bot.services.scheduler import schedule_reminder, scheduler
from bot.services.timezone_ctx import get_effective_timezone

router = Router()


@router.callback_query(lambda c: c.data and (c.data.startswith("confirm:") or c.data.startswith("confirm_edit:")))
async def confirm_reminder(callback: CallbackQuery, bot: Bot) -> None:
    is_edit = callback.data.startswith("confirm_edit:")
    if is_edit:
        _, reminder_id_str, draft_id = callback.data.split(":", 2)
        reminder_id = int(reminder_id_str)
    else:
        draft_id = callback.data.split(":", 1)[1]
        reminder_id = None

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

        if is_edit and reminder_id is not None:
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
            return

        tz = await get_effective_timezone(
            session, callback.message.chat.id, callback.from_user.id
        )
        next_run = compute_next_run(entry.parsed, tz)

        duplicate = await find_duplicate_reminder(
            session,
            callback.message.chat.id,
            entry.parsed.text,
            entry.parsed.kind,
            created_by=callback.from_user.id,
        )
        if duplicate:
            await callback.answer(
                f"Похожее напоминание уже есть (#{duplicate.id}). Используй /edit {duplicate.id}",
                show_alert=True,
            )
            return

        reminder = await create_reminder(
            session,
            user_id=user.id,
            chat_id=callback.message.chat.id,
            created_by_telegram_id=callback.from_user.id,
            timezone=tz,
            text=entry.parsed.text,
            kind=entry.parsed.kind,
            next_run_at=next_run,
            interval_seconds=entry.parsed.interval_seconds,
            daily_time=entry.parsed.daily_time,
            weekdays_mask=weekdays_to_mask(entry.parsed.weekdays) if entry.parsed.weekdays else None,
            mention_telegram_id=entry.mention_telegram_id,
        )

    schedule_reminder(bot, reminder.id, next_run)
    when = next_run.astimezone(ZoneInfo(tz)).strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(format_created(reminder.id, when, entry.parsed.text))
    await callback.message.answer("Меню:", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("cancel:"))
async def cancel_draft(callback: CallbackQuery) -> None:
    draft_id = callback.data.split(":", 1)[1]
    discard_draft(draft_id, callback.from_user.id)
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("snooze:"))
async def snooze_reminder(callback: CallbackQuery, bot: Bot) -> None:
    _, reminder_id_str, minutes_str = callback.data.split(":")
    reminder_id = int(reminder_id_str)
    minutes = int(minutes_str)

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

    schedule_reminder(bot, reminder_id, next_run)
    await callback.message.edit_text(
        f"⏰ Отложено на {minutes} мин.\nНапоминание: {reminder.text}"
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

    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    await callback.message.edit_text("✅ Готово. Напоминание закрыто.")
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

    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    await callback.message.edit_text("🗑 Напоминание удалено.")
    await callback.answer()
