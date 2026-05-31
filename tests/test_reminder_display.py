from datetime import datetime, time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from bot.services.reminder_display import (
    format_interval_seconds,
    format_parsed_when_label,
    format_reminder_list_line,
    format_weekdays_label,
    reminder_to_export_dict,
)
from bot.services.nlp.schemas import ParsedReminder


def _reminder(**kwargs):
    defaults = dict(
        id=1,
        text="зарядка",
        kind="daily",
        timezone="Europe/Moscow",
        next_run_at=None,
        interval_seconds=None,
        daily_time=time(9, 0),
        weekdays_mask=None,
        mention_telegram_id=None,
        chat_id=123,
        created_by_telegram_id=1,
        is_active=True,
        created_at=datetime(2025, 1, 1),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_format_interval():
    assert "2 ч." in format_interval_seconds(7200)
    assert "30 мин." in format_interval_seconds(1800)


def test_format_weekdays_mask():
    assert format_weekdays_label(mask=0b10101) == "пн, ср, пт"
    assert format_weekdays_label(mask=0b11111) == "по будням"


def test_format_parsed_when_label_delay():
    parsed = ParsedReminder(text="созвон", kind="once", delay_seconds=120)
    assert format_parsed_when_label(parsed, "Europe/Moscow") == "через 2 мин от подтверждения"


def test_format_parsed_when_label_weekly():
    parsed = ParsedReminder(
        text="Экспа",
        kind="weekly",
        daily_time=time(10, 55),
        weekdays=[1, 2, 4, 5],
    )
    assert format_parsed_when_label(parsed, "Europe/Moscow") == "вт, ср, пт, сб в 10:55"


def test_list_line_interval():
    r = _reminder(
        kind="interval",
        interval_seconds=3600,
        next_run_at=datetime(2030, 6, 1, 14, 30, tzinfo=ZoneInfo("Europe/Moscow")),
        daily_time=None,
    )
    line = format_reminder_list_line(r)
    assert "каждые 1 ч." in line
    assert "14:30" in line or "14.06" in line


def test_export_dict_has_mention():
    r = _reminder(mention_telegram_id=42)
    d = reminder_to_export_dict(r)
    assert d["mention_telegram_id"] == 42
