import json
from datetime import datetime, time
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import select

from bot.config import settings
from bot.db.models import Reminder
from bot.db.repository import (
    async_session,
    create_reminder,
    deactivate_all_chat_reminders,
    get_active_chat_reminders,
    get_or_create_user,
)
from bot.keyboards.inline import clear_confirm_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import compute_next_run, mask_to_weekdays, weekdays_to_mask
from bot.services.scheduler import schedule_reminder, scheduler

router = Router()


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.chat_id == message.chat.id, Reminder.is_active.is_(True))
            .order_by(Reminder.created_at.desc())
        )
        reminders = list(result.scalars().all())

    data = [
        {
            "id": r.id,
            "chat_id": r.chat_id,
            "created_by_telegram_id": r.created_by_telegram_id,
            "timezone": r.timezone,
            "text": r.text,
            "kind": r.kind,
            "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
            "interval_seconds": r.interval_seconds,
            "daily_time": r.daily_time.strftime("%H:%M") if r.daily_time else None,
            "weekdays_mask": r.weekdays_mask,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reminders
    ]

    payload = json.dumps(
        {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "chat_id": message.chat.id,
            "reminders": data,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    file = BufferedInputFile(payload, filename="reminders_export.json")
    await message.answer_document(file)


@router.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    async with async_session() as session:
        count = len(await get_active_chat_reminders(session, message.chat.id))

    if count == 0:
        await message.answer("Активных напоминаний нет.")
        return

    await message.answer(
        f"Удалить все активные напоминания в этом чате ({count} шт.)?",
        reply_markup=clear_confirm_keyboard(),
    )


@router.callback_query(F.data == "clear:no")
async def clear_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(F.data == "clear:yes")
async def clear_confirm(callback: CallbackQuery, bot: Bot) -> None:
    async with async_session() as session:
        reminders = await get_active_chat_reminders(session, callback.message.chat.id)
        count = await deactivate_all_chat_reminders(session, callback.message.chat.id)

    for reminder in reminders:
        job_id = f"reminder_{reminder.id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    await callback.message.edit_text(f"🗑 Удалено напоминаний: {count}")
    await callback.answer()


@router.message(Command("import"))
async def cmd_import(message: Message, bot: Bot) -> None:
    document = message.document
    if document is None and message.reply_to_message:
        document = message.reply_to_message.document

    if document is None:
        await message.answer(
            "Пришли JSON-файл (из /export) документом или ответь /import на сообщение с файлом."
        )
        return

    tg_file = await bot.get_file(document.file_id)
    downloaded = await bot.download_file(tg_file.file_path)
    raw = downloaded.read() if hasattr(downloaded, "read") else downloaded

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await message.answer("Не удалось прочитать JSON.")
        return

    items = data.get("reminders", data if isinstance(data, list) else [])
    if not items:
        await message.answer("В файле нет напоминаний.")
        return

    imported = 0
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            timezone=settings.default_timezone,
        )
        for item in items:
            if not item.get("is_active", True):
                continue
            kind = item.get("kind", "once")
            text_val = str(item.get("text", "")).strip()
            if not text_val:
                continue

            tz = item.get("timezone") or user.timezone
            daily_time = None
            if item.get("daily_time"):
                h, m = str(item["daily_time"]).split(":")
                daily_time = time(int(h), int(m))

            weekdays_mask = item.get("weekdays_mask")
            weekdays_list = mask_to_weekdays(weekdays_mask) if weekdays_mask else None

            next_run_at = None
            if item.get("next_run_at"):
                next_run_at = datetime.fromisoformat(str(item["next_run_at"]).replace("Z", "+00:00"))

            parsed = ParsedReminder(
                text=text_val,
                kind=kind,
                run_at=next_run_at,
                interval_seconds=item.get("interval_seconds"),
                daily_time=daily_time,
                weekdays=weekdays_list,
            )
            try:
                next_run = compute_next_run(parsed, tz)
            except Exception:
                continue

            reminder = await create_reminder(
                session,
                user_id=user.id,
                chat_id=message.chat.id,
                created_by_telegram_id=message.from_user.id,
                timezone=tz,
                text=text_val,
                kind=kind,
                next_run_at=next_run,
                interval_seconds=item.get("interval_seconds"),
                daily_time=daily_time,
                weekdays_mask=weekdays_mask or (weekdays_to_mask(weekdays_list) if weekdays_list else None),
            )
            schedule_reminder(bot, reminder.id, next_run)
            imported += 1

    await message.answer(
        f"✅ Импортировано напоминаний: {imported}",
        reply_markup=main_menu_keyboard(),
    )

