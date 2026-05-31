from datetime import UTC, datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import User
from bot.db.repository import async_session, get_all_active_reminders
from bot.services.auto_update import fetch_remote_sha
from bot.services.deploy_meta import read_deploy_sha
from bot.services.reminder_utils import local_run_at
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

    now = datetime.now(UTC)
    async with async_session() as session:
        users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        active_reminders = await get_all_active_reminders(session)
        overdue = 0
        for r in active_reminders:
            nxt = local_run_at(r.next_run_at, r.timezone)
            if nxt is not None and nxt.astimezone(UTC) <= now:
                overdue += 1
        with_schedule = sum(1 for r in active_reminders if r.next_run_at is not None)

    scheduled_jobs = count_scheduled_reminder_jobs()
    drift = abs(scheduled_jobs - with_schedule)
    if drift <= 2:
        status_label = "✅ норма"
    else:
        status_label = "⚠️ рассинхрон"

    scheduler_state = "работает" if scheduler.running else "остановлен"
    local_sha = read_deploy_sha()
    remote_sha = await fetch_remote_sha()
    deploy_line = ""
    if local_sha or remote_sha:
        local_label = local_sha[:7] if local_sha else "—"
        remote_label = remote_sha[:7] if remote_sha else "—"
        deploy_line = f"Deploy: <code>{local_label}</code> → GitHub <code>{remote_label}</code>\n"

    await message.answer(
        "🩺 <b>Состояние сервера</b>\n\n"
        f"Статус: <b>{status_label}</b>\n"
        f"Версия: <b>{__version__}</b>\n"
        f"{deploy_line}"
        f"Аптайм: <b>{format_uptime(uptime_seconds())}</b>\n"
        f"Пользователей: <b>{users_count}</b>\n"
        f"Активных напоминаний: <b>{len(active_reminders)}</b>\n"
        f"С расписанием: <b>{with_schedule}</b>\n"
        f"Просрочено в БД: <b>{overdue}</b>\n"
        f"Задач планировщика: <b>{scheduled_jobs}</b>\n"
        f"Планировщик: <b>{scheduler_state}</b>"
    )
