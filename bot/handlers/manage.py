import json
from datetime import datetime
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
from bot.services.export_import import parse_import_item
from bot.services.reminder_display import reminder_to_export_dict
from bot.services.reminder_utils import compute_next_run, weekdays_to_mask
from bot.services.scheduler import schedule_reminder, scheduler

router = Router()

MAX_SKIP_REASONS = 5


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.chat_id == message.chat.id, Reminder.is_active.is_(True))
            .order_by(Reminder.created_at.desc())
        )
        reminders = list(result.scalars().all())

    data = [reminder_to_export_dict(r) for r in reminders]

    payload = json.dumps(
        {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "chat_id": message.chat.id,
            "version": 2,
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
    skipped_inactive = 0
    skip_reasons: list[str] = []

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            timezone=settings.default_timezone,
        )
        for idx, item in enumerate(items, start=1):
            if not item.get("is_active", True):
                skipped_inactive += 1
                continue

            try:
                result = parse_import_item(item, user.timezone)
                next_run = compute_next_run(result.parsed, result.timezone)
            except Exception as exc:
                label = item.get("text", "")[:30] or f"строка {idx}"
                skip_reasons.append(f"«{label}»: {exc}")
                continue

            weekdays_mask = result.weekdays_mask
            if weekdays_mask is None and result.parsed.weekdays:
                weekdays_mask = weekdays_to_mask(result.parsed.weekdays)

            reminder = await create_reminder(
                session,
                user_id=user.id,
                chat_id=message.chat.id,
                created_by_telegram_id=message.from_user.id,
                timezone=result.timezone,
                text=result.parsed.text,
                kind=result.parsed.kind,
                next_run_at=next_run,
                interval_seconds=result.parsed.interval_seconds,
                daily_time=result.parsed.daily_time,
                weekdays_mask=weekdays_mask,
                mention_telegram_id=result.mention_telegram_id,
            )
            schedule_reminder(bot, reminder.id, next_run)
            imported += 1

    lines = [f"✅ Импортировано: {imported}"]
    if skipped_inactive:
        lines.append(f"⏭ Пропущено неактивных: {skipped_inactive}")
    if skip_reasons:
        lines.append(f"⚠️ Ошибки ({len(skip_reasons)}):")
        lines.extend(f"• {r}" for r in skip_reasons[:MAX_SKIP_REASONS])
        if len(skip_reasons) > MAX_SKIP_REASONS:
            lines.append(f"• … и ещё {len(skip_reasons) - MAX_SKIP_REASONS}")

    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())
