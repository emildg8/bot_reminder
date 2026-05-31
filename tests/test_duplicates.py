from datetime import datetime, time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from bot.services.duplicates import normalize_text, schedules_match
from bot.services.nlp.schemas import ParsedReminder


def _reminder(**kwargs):
    defaults = dict(
        id=1,
        text="созвон",
        kind="once",
        timezone="Europe/Moscow",
        next_run_at=datetime(2030, 6, 15, 14, 0, tzinfo=ZoneInfo("Europe/Moscow")),
        interval_seconds=None,
        daily_time=None,
        weekdays_mask=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_normalize_text():
    assert normalize_text("  Hello   World  ") == "hello world"


def test_same_text_different_time_not_duplicate():
    reminder = _reminder(
        next_run_at=datetime(2030, 6, 15, 14, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    parsed = ParsedReminder(
        text="созвон",
        kind="once",
        run_at=datetime(2030, 6, 16, 14, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    assert schedules_match(reminder, parsed, "Europe/Moscow") is False


def test_same_text_same_time_is_duplicate():
    run_at = datetime(2030, 6, 15, 14, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    reminder = _reminder(next_run_at=run_at)
    parsed = ParsedReminder(text="созвон", kind="once", run_at=run_at)
    assert schedules_match(reminder, parsed, "Europe/Moscow") is True


def test_relative_delay_never_matches_existing():
    reminder = _reminder(
        next_run_at=datetime(2030, 6, 15, 14, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    parsed = ParsedReminder(text="созвон", kind="once", delay_seconds=300)
    assert schedules_match(reminder, parsed, "Europe/Moscow") is False


def test_weekly_schedule_match():
    reminder = _reminder(
        kind="weekly",
        next_run_at=None,
        daily_time=time(9, 0),
        weekdays_mask=0b11111,
    )
    parsed = ParsedReminder(
        text="стендап",
        kind="weekly",
        daily_time=time(9, 0),
        weekdays=[0, 1, 2, 3, 4],
    )
    assert schedules_match(reminder, parsed, "Europe/Moscow") is True
