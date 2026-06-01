from datetime import UTC, datetime, timedelta

from bot.services.scheduler import compute_restore_run_at, count_scheduled_reminder_jobs, schedule_reminder
from unittest.mock import MagicMock


def test_compute_restore_run_at_jitter():
    now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    t0 = compute_restore_run_at(now, 0)
    t1 = compute_restore_run_at(now, 1)
    assert t0 >= now
    assert t1 >= t0


def test_count_scheduled_reminder_jobs():
    bot = MagicMock()
    schedule_reminder(bot, 999001, datetime.now(UTC) + timedelta(hours=1), timezone="UTC")
    assert count_scheduled_reminder_jobs() >= 1
