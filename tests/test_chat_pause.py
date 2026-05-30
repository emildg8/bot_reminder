from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from bot.db.models import Reminder, ReminderKind
from bot.services.reminder_utils import resolve_next_run_on_resume


def _make_reminder(**kwargs) -> Reminder:
    defaults = {
        "id": 1,
        "user_id": 1,
        "chat_id": 1,
        "created_by_telegram_id": 1,
        "text": "test",
        "timezone": "Europe/Moscow",
        "kind": ReminderKind.DAILY.value,
        "daily_time": time(9, 0),
        "interval_seconds": None,
        "weekdays_mask": None,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Reminder(**defaults)


def test_resume_past_daily_recalculates():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    past = now - timedelta(hours=2)
    reminder = _make_reminder(next_run_at=past)

    next_run = resolve_next_run_on_resume(reminder, now)
    assert next_run is not None
    assert next_run > now


def test_resume_future_unchanged():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    future = now + timedelta(hours=3)
    reminder = _make_reminder(next_run_at=future)

    next_run = resolve_next_run_on_resume(reminder, now)
    assert next_run == future


def test_resume_past_once_schedules_soon():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    past = now - timedelta(hours=1)
    reminder = _make_reminder(
        kind=ReminderKind.ONCE.value,
        next_run_at=past,
        daily_time=None,
    )

    next_run = resolve_next_run_on_resume(reminder, now)
    assert next_run is not None
    assert next_run > now
    assert (next_run - now).total_seconds() <= 120
