"""Отмена задач APScheduler для напоминаний."""

from __future__ import annotations

from bot.services.scheduler import scheduler


def cancel_reminder_job(reminder_id: int) -> bool:
    job_id = f"reminder_{reminder_id}"
    job = scheduler.get_job(job_id)
    if job is None:
        return False
    scheduler.remove_job(job_id)
    return True
