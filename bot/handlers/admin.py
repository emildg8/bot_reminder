from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
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

