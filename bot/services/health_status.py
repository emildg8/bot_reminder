"""Сбор метрик для /health."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.db.repository import get_all_active_reminders
from bot.services.reminder_utils import local_run_at
from bot.services.scheduler import RepairStats, count_scheduled_reminder_jobs, repair_reminder_jobs, scheduler


@dataclass
class HealthSnapshot:
    users_count: int
    active_count: int
    with_schedule: int
    overdue: int
    scheduled_jobs: int
    drift: int
    scheduler_running: bool

    @property
    def needs_repair(self) -> bool:
        return self.overdue > 0 or self.drift > 2


async def collect_health_snapshot(session: AsyncSession) -> HealthSnapshot:
    now = datetime.now(UTC)
    users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    active_reminders = await get_all_active_reminders(session)

    overdue = 0
    for reminder in active_reminders:
        nxt = local_run_at(reminder.next_run_at, reminder.timezone)
        if nxt is not None and nxt.astimezone(UTC) <= now:
            overdue += 1

    with_schedule = sum(1 for r in active_reminders if r.next_run_at is not None)
    scheduled_jobs = count_scheduled_reminder_jobs()
    drift = abs(scheduled_jobs - with_schedule)

    return HealthSnapshot(
        users_count=users_count,
        active_count=len(active_reminders),
        with_schedule=with_schedule,
        overdue=overdue,
        scheduled_jobs=scheduled_jobs,
        drift=drift,
        scheduler_running=scheduler.running,
    )


def format_health_message(
    snapshot: HealthSnapshot,
    *,
    version: str,
    uptime: str,
    deploy_line: str,
    repair: RepairStats | None = None,
) -> str:
    if snapshot.drift <= 2:
        status_label = "✅ норма"
    else:
        status_label = "⚠️ рассинхрон"

    scheduler_state = "работает" if snapshot.scheduler_running else "остановлен"
    repair_line = ""
    if repair is not None and (repair.overdue_rescheduled or repair.missing_job_fixed):
        repair_line = (
            f"🔧 Перепланировано: <b>{repair.overdue_rescheduled}</b> просроч., "
            f"<b>{repair.missing_job_fixed}</b> без задачи\n"
        )

    return (
        "🩺 <b>Состояние сервера</b>\n\n"
        f"Статус: <b>{status_label}</b>\n"
        f"Версия: <b>{version}</b>\n"
        f"{deploy_line}"
        f"Аптайм: <b>{uptime}</b>\n"
        f"Пользователей: <b>{snapshot.users_count}</b>\n"
        f"Активных напоминаний: <b>{snapshot.active_count}</b>\n"
        f"С расписанием: <b>{snapshot.with_schedule}</b>\n"
        f"Просрочено в БД: <b>{snapshot.overdue}</b>\n"
        f"Задач планировщика: <b>{snapshot.scheduled_jobs}</b>\n"
        f"Планировщик: <b>{scheduler_state}</b>\n"
        f"{repair_line}"
    )


async def run_health_check(bot: Bot) -> tuple[HealthSnapshot, RepairStats | None]:
    from bot.db.repository import async_session

    async with async_session() as session:
        snapshot = await collect_health_snapshot(session)

    repair: RepairStats | None = None
    if snapshot.needs_repair:
        repair = await repair_reminder_jobs(bot)
        async with async_session() as session:
            snapshot = await collect_health_snapshot(session)

    return snapshot, repair
