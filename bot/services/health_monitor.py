"""Фоновый мониторинг здоровья scheduler — алерт админам при repair."""

from __future__ import annotations

import logging
import time

from aiogram import Bot

from bot.config import settings
from bot.services.health_status import run_health_check

logger = logging.getLogger(__name__)

_last_alert_at: float = 0.0
_ALERT_COOLDOWN_SEC = 3600


async def run_health_monitor(bot: Bot) -> None:
    """Периодическая проверка; при repair или persistent drift — DM админам."""
    global _last_alert_at

    if not settings.admin_telegram_ids:
        return

    snapshot, repair = await run_health_check(bot)

    now = time.monotonic()
    if repair and (repair.overdue_rescheduled or repair.missing_job_fixed):
        text = (
            "🔧 <b>Scheduler repair</b>\n"
            f"Просрочено перепланировано: <b>{repair.overdue_rescheduled}</b>\n"
            f"Восстановлено задач: <b>{repair.missing_job_fixed}</b>"
        )
        await _notify_admins(bot, text)
        _last_alert_at = now
        return

    if snapshot.needs_repair and now - _last_alert_at >= _ALERT_COOLDOWN_SEC:
        text = (
            "⚠️ <b>Scheduler drift</b>\n"
            f"Просрочено: <b>{snapshot.overdue}</b> · "
            f"drift: <b>{snapshot.drift}</b> · "
            f"jobs: <b>{snapshot.scheduled_jobs}</b>/<b>{snapshot.with_schedule}</b>\n"
            "Запусти /health для деталей."
        )
        await _notify_admins(bot, text)
        _last_alert_at = now


async def _notify_admins(bot: Bot, text: str) -> None:
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.warning("Health monitor: cannot notify admin %s: %s", admin_id, exc)
