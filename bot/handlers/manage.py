import json
import re
from datetime import datetime

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
    get_reminder,
)
from bot.keyboards.inline import clear_confirm_keyboard, delete_confirm_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_permissions import can_manage_group_reminders
from bot.services.export_import import parse_import_item
from bot.services.reminder_display import reminder_to_export_dict
from bot.services.reminder_utils import compute_next_run, weekdays_to_mask
from bot.services.chat_delivery import format_ops_target_note, resolve_delivery_chat_id
from bot.services.reminder_jobs import teardown_reminder_schedule

from bot.services.scheduler import schedule_reminder

router = Router()

DELETE_CMD_PATTERN = re.compile(
    r"^/(?:delete|del)(?:@\w+)?(?:\s+#?(\d+))?$",
    re.IGNORECASE,
)


async def _ops_chat_id(message: Message) -> int:
    async with async_session() as session:
        return await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )

MAX_SKIP_REASONS = 5


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    async with async_session() as session:
        ops_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )
        result = await session.execute(
            select(Reminder)
            .where(Reminder.chat_id == ops_id, Reminder.is_active.is_(True))
            .order_by(Reminder.created_at.desc())
        )
        reminders = list(result.scalars().all())

    data = [reminder_to_export_dict(r) for r in reminders]

    payload = json.dumps(
        {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "chat_id": ops_id,
            "version": 2,
            "reminders": data,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    file = BufferedInputFile(payload, filename="reminders_export.json")
    await message.answer_document(file)


@router.message(lambda m: m.text and DELETE_CMD_PATTERN.match(m.text.strip()))
async def cmd_delete(message: Message, bot: Bot) -> None:
    match = DELETE_CMD_PATTERN.match(message.text.strip())
    reminder_id_str = match.group(1)
    if reminder_id_str is None:
        await message.answer(
            "Формат:\n"
            "<code>/delete 24</code> или <code>/del 24</code>\n\n"
            "Удаляет только <b>твоё</b> напоминание из /list.\n"
            "В группе кнопки 🗑 нет — используй команду.",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    reminder_id = int(reminder_id_str)

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await message.answer("Напоминание не найдено.")
            return
        if reminder.created_by_telegram_id != message.from_user.id:
            await message.answer("Можно удалять только свои напоминания.")
            return

    await message.answer(
        f"🗑 Удалить напоминание #{reminder_id}?\n📝 {reminder.text}",
        reply_markup=delete_confirm_keyboard(reminder_id),
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message, bot: Bot) -> None:
    if not await can_manage_group_reminders(bot, message.chat.id, message.from_user.id):
        await message.answer(
            "В группе удалять все напоминания могут только администраторы чата.",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    async with async_session() as session:
        ops_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )
        count = len(await get_active_chat_reminders(session, ops_id))

    if count == 0:
        await message.answer("Активных напоминаний нет.")
        return

    note = format_ops_target_note(message.chat.id, ops_id)
    await message.answer(
        f"Удалить все активные напоминания ({count} шт.)?{note}",
        reply_markup=clear_confirm_keyboard(),
    )


@router.callback_query(F.data == "clear:no")
async def clear_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Отменено.")
    await callback.answer()


@router.callback_query(F.data == "clear:yes")
async def clear_confirm(callback: CallbackQuery, bot: Bot) -> None:
    if not await can_manage_group_reminders(
        bot, callback.message.chat.id, callback.from_user.id
    ):
        await callback.answer("Только для администраторов чата.", show_alert=True)
        return

    async with async_session() as session:
        ops_id = await resolve_delivery_chat_id(
            session, callback.message.chat.id, callback.message.chat.type
        )
        reminders = await get_active_chat_reminders(session, ops_id)
        for reminder in reminders:
            await teardown_reminder_schedule(bot, session, reminder)
        count = await deactivate_all_chat_reminders(session, ops_id)

    note = format_ops_target_note(callback.message.chat.id, ops_id)
    await callback.message.edit_text(f"🗑 Удалено напоминаний: {count}{note}")
    await callback.answer()


@router.message(Command("pause"))
async def cmd_pause(message: Message, bot: Bot) -> None:
    from bot.services.chat_pause import pause_chat_reminders

    if not await can_manage_group_reminders(bot, message.chat.id, message.from_user.id):
        await message.answer(
            "В группе ставить на паузу могут только администраторы чата.",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    ops_id = await _ops_chat_id(message)
    count = await pause_chat_reminders(bot, ops_id)
    if count == 0:
        await message.answer("Активных напоминаний нет.")
        return
    note = format_ops_target_note(message.chat.id, ops_id)
    await message.answer(
        f"⏸ Напоминания на паузе ({count} шт.).\n"
        f"Срабатывания остановлены. Возобновить: /resume{note}",
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )


@router.message(Command("resume"))
async def cmd_resume(message: Message, bot: Bot) -> None:
    from bot.services.chat_pause import resume_chat_reminders

    if not await can_manage_group_reminders(bot, message.chat.id, message.from_user.id):
        await message.answer(
            "В группе возобновлять могут только администраторы чата.",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    ops_id = await _ops_chat_id(message)
    count = await resume_chat_reminders(bot, ops_id)
    note = format_ops_target_note(message.chat.id, ops_id)
    await message.answer(
        f"▶️ Напоминания возобновлены ({count} в расписании).{note}",
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )


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
        ops_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
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
                chat_id=ops_id,
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
            schedule_reminder(bot, reminder.id, next_run, timezone=result.timezone)
            imported += 1

    lines = [f"✅ Импортировано: {imported}"]
    if skipped_inactive:
        lines.append(f"⏭ Пропущено неактивных: {skipped_inactive}")
    if skip_reasons:
        lines.append(f"⚠️ Ошибки ({len(skip_reasons)}):")
        lines.extend(f"• {r}" for r in skip_reasons[:MAX_SKIP_REASONS])
        if len(skip_reasons) > MAX_SKIP_REASONS:
            lines.append(f"• … и ещё {len(skip_reasons) - MAX_SKIP_REASONS}")

    await message.answer("\n".join(lines), reply_markup=menu_keyboard_for_chat(message.chat.id))
