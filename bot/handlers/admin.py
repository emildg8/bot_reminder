import json
from datetime import datetime
from io import BytesIO

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import Reminder, User
from bot.db.repository import async_session

router = Router()


def _is_admin(user_id: int) -> bool:
    return bool(settings.admin_telegram_ids) and user_id in set(settings.admin_telegram_ids)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только админам.")
        return

    async with async_session() as session:
        users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        reminders_total = (await session.execute(select(func.count()).select_from(Reminder))).scalar_one()
        reminders_active = (
            await session.execute(select(func.count()).select_from(Reminder).where(Reminder.is_active.is_(True)))
        ).scalar_one()

    await message.answer(
        "📊 Статистика\n"
        f"- Users: {users_count}\n"
        f"- Reminders total: {reminders_total}\n"
        f"- Reminders active: {reminders_active}\n"
    )


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    # export reminders for current chat (works for groups and private)
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

    bio = BytesIO(payload)
    file = BufferedInputFile(bio.getvalue(), filename="reminders_export.json")
    await message.answer_document(file)

