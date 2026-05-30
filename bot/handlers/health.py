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
    await message.answer(f"✅ ok · v{__version__} · uptime {format_uptime(uptime_seconds())}")


@router.message(Command("health"))
async def cmd_health(message: Message) -> None:
    if not settings.admin_telegram_ids or message.from_user.id not in settings.admin_telegram_ids:
        await message.answer("Команда доступна только админам.")
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
    status = "ok" if drift <= 2 else "degraded"

    await message.answer(
        "🩺 Health\n"
        f"- status: {status}\n"
        f"- version: {__version__}\n"
        f"- uptime: {format_uptime(uptime_seconds())}\n"
        f"- users: {users_count}\n"
        f"- active reminders: {len(active_reminders)}\n"
        f"- with next_run_at: {with_schedule}\n"
        f"- overdue in db: {overdue}\n"
        f"- scheduled jobs: {scheduled_jobs}\n"
        f"- scheduler: {'running' if scheduler.running else 'stopped'}\n"
    )
