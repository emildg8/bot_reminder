from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import Reminder, User
from bot.db.repository import async_session, get_all_active_reminders
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.runtime import format_uptime, uptime_seconds
from bot.services.scheduler import scheduler
from bot.version import __version__

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
        reminders_active = len(await get_all_active_reminders(session))

    scheduled_jobs = len([j for j in scheduler.get_jobs() if j.id.startswith("reminder_")])

    await message.answer(
        "📊 Статистика\n"
        f"- Version: {__version__}\n"
        f"- Uptime: {format_uptime(uptime_seconds())}\n"
        f"- Users: {users_count}\n"
        f"- Reminders total: {reminders_total}\n"
        f"- Reminders active: {reminders_active}\n"
        f"- Scheduled jobs: {scheduled_jobs}\n"
    )


@router.message(Command("setavatar"))
async def cmd_setavatar(message: Message, bot: Bot) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только админам.")
        return

    await message.answer("⏳ Загружаю аватар...")
    try:
        await ensure_bot_avatar(bot, force=True)
        await message.answer("✅ Аватар обновлён. Проверь профиль бота.")
    except Exception as exc:
        await message.answer(f"❌ Не удалось: {exc}")
