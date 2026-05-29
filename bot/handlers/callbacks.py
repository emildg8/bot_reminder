from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from zoneinfo import ZoneInfo

from bot.db.models import User
from bot.db.repository import (
    async_session,
    create_reminder,
    deactivate_reminder,
    get_or_create_user,
    get_reminder,
    update_reminder_next_run,
)
from bot.services.drafts import discard_draft, pop_draft
from bot.services.reminder_utils import compute_next_run
from bot.services.scheduler import schedule_reminder, scheduler

router = Router()


async def _get_reminder_owner(session, reminder) -> User | None:
    result = await session.execute(select(User).where(User.id == reminder.user_id))
    return result.scalar_one_or_none()


@router.callback_query(lambda c: c.data and c.data.startswith("confirm:"))
async def confirm_reminder(callback: CallbackQuery, bot: Bot) -> None:
    draft_id = callback.data.split(":", 1)[1]
    parsed = pop_draft(draft_id, callback.from_user.id)
    if parsed is None:
        await callback.answer("Черновик не найден или устарел.", show_alert=True)
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone="Europe/Moscow",
        )
        next_run = compute_next_run(parsed, user.timezone)
        reminder = await create_reminder(
            session,
            user_id=user.id,
            text=parsed.text,
            kind=parsed.kind,
            next_run_at=next_run,
            interval_seconds=parsed.interval_seconds,
            daily_time=parsed.daily_time,
        )

    schedule_reminder(bot, reminder.id, next_run)
    when = next_run.astimezone(ZoneInfo(user.timezone)).strftime("%d.%m.%Y %H:%M")
    await callback.message.edit_text(f"✅ Напоминание создано (#{reminder.id}). Первый раз: {when}")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("cancel:"))
async def cancel_draft(callback: CallbackQuery) -> None:
    draft_id = callback.data.split(":", 1)[1]
    discard_draft(draft_id)
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("snooze:"))
async def snooze_reminder(callback: CallbackQuery, bot: Bot) -> None:
    _, reminder_id_str, minutes_str = callback.data.split(":")
    reminder_id = int(reminder_id_str)
    minutes = int(minutes_str)

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await callback.answer("Напоминание не найдено.", show_alert=True)
            return

        user = await _get_reminder_owner(session, reminder)
        if user is None or user.telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        tz = ZoneInfo(user.timezone)
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

        user = await _get_reminder_owner(session, reminder)
        if user is None or user.telegram_id != callback.from_user.id:
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

        user = await _get_reminder_owner(session, reminder)
        if user is None or user.telegram_id != callback.from_user.id:
            await callback.answer("Нет доступа.", show_alert=True)
            return

        await deactivate_reminder(session, reminder)

    job_id = f"reminder_{reminder_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    await callback.message.edit_text("🗑 Напоминание удалено.")
    await callback.answer()
