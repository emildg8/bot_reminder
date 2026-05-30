from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import Reminder, User
from bot.db.repository import async_session, get_all_active_reminders
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.media import describe_stt_backends, is_ffmpeg_available
from bot.services.runtime import format_uptime, uptime_seconds
from bot.services.scheduler import scheduler
from bot.version import __version__

router = Router()


def _is_admin(user_id: int) -> bool:
    return bool(settings.admin_telegram_ids) and user_id in set(settings.admin_telegram_ids)


@router.message(Command("sysinfo"))
async def cmd_sysinfo(message: Message) -> None:
    """Системная статистика — только для админов бота."""
    if not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    async with async_session() as session:
        users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        reminders_total = (await session.execute(select(func.count()).select_from(Reminder))).scalar_one()
        reminders_active = len(await get_all_active_reminders(session))

    scheduled_jobs = len([j for j in scheduler.get_jobs() if j.id.startswith("reminder_")])
    ffmpeg_ok = is_ffmpeg_available()
    stt_chain = describe_stt_backends()

    await message.answer(
        "🛠 <b>Системная статистика</b>\n\n"
        f"Версия: <b>{__version__}</b>\n"
        f"Аптайм: <b>{format_uptime(uptime_seconds())}</b>\n"
        f"Пользователей: <b>{users_count}</b>\n"
        f"Напоминаний всего: <b>{reminders_total}</b>\n"
        f"Активных: <b>{reminders_active}</b>\n"
        f"Задач в планировщике: <b>{scheduled_jobs}</b>\n\n"
        f"ffmpeg: <b>{'да' if ffmpeg_ok else 'нет'}</b>\n"
        f"STT: <code>{stt_chain}</code>"
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
