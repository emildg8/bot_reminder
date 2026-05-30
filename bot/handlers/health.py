from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import User
from bot.db.repository import async_session, get_all_active_reminders
from bot.services.runtime import format_uptime, uptime_seconds
from bot.services.scheduler import count_scheduled_reminder_jobs, scheduler
from bot.version import __version__

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    uptime = format_uptime(uptime_seconds())
    await message.answer(f"✅ Бот работает · v{__version__} · аптайм {uptime}")


@router.message(Command("health"))
async def cmd_health(message: Message) -> None:
    if not settings.admin_telegram_ids or message.from_user.id not in settings.admin_telegram_ids:
        await message.answer("Команда доступна только администраторам бота.")
        return

    now = datetime.now().astimezone()
    async with async_session() as session:
        users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        active_reminders = await get_all_active_reminders(session)
        overdue = sum(
            1
            for r in active_reminders
            if r.next_run_at is not None
            and (r.next_run_at if r.next_run_at.tzinfo else r.next_run_at.replace(tzinfo=now.tzinfo))
            <= now
        )
        with_schedule = sum(1 for r in active_reminders if r.next_run_at is not None)

    scheduled_jobs = count_scheduled_reminder_jobs()
    drift = abs(scheduled_jobs - with_schedule)
    if drift <= 2:
        status_label = "✅ норма"
    else:
        status_label = "⚠️ рассинхрон"

    scheduler_state = "работает" if scheduler.running else "остановлен"

    await message.answer(
        "🩺 <b>Состояние сервера</b>\n\n"
        f"Статус: <b>{status_label}</b>\n"
        f"Версия: <b>{__version__}</b>\n"
        f"Аптайм: <b>{format_uptime(uptime_seconds())}</b>\n"
        f"Пользователей: <b>{users_count}</b>\n"
        f"Активных напоминаний: <b>{len(active_reminders)}</b>\n"
        f"С расписанием: <b>{with_schedule}</b>\n"
        f"Просрочено в БД: <b>{overdue}</b>\n"
        f"Задач планировщика: <b>{scheduled_jobs}</b>\n"
        f"Планировщик: <b>{scheduler_state}</b>"
    )
