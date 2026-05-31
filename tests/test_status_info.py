from datetime import datetime
from zoneinfo import ZoneInfo

from bot.db.models import Reminder
from bot.services.reminder_jobs import cancel_reminder_job
from bot.services.scheduler import scheduler
from bot.services.status_info import format_next_reminder_line


def test_format_next_reminder_line():
    reminder = Reminder(
        id=7,
        user_id=1,
        chat_id=-100,
        created_by_telegram_id=1,
        timezone="Europe/Moscow",
        text="созвон",
        kind="once",
        next_run_at=datetime(2030, 6, 15, 14, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    line = format_next_reminder_line([reminder], "Europe/Moscow")
    assert line is not None
    assert "#7" in line
    assert "созвон" in line


def test_cancel_reminder_job_missing():
    assert cancel_reminder_job(999_999_999) is False


def test_cancel_reminder_job_removes():
    from datetime import UTC, timedelta

    from apscheduler.triggers.date import DateTrigger

    run_at = datetime.now(UTC) + timedelta(hours=1)
    scheduler.add_job(
        lambda: None,
        trigger=DateTrigger(run_date=run_at),
        id="reminder_4242",
    )
    assert cancel_reminder_job(4242) is True
    assert scheduler.get_job("reminder_4242") is None
