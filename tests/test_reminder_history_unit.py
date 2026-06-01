from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from bot.db.models import ReminderEvent, ReminderEventKind
from bot.services.reminder_history import (
    MonthStats,
    _event_label,
    format_day_journal,
    format_month_stats,
    get_month_stats,
    log_reminder_event,
)


def test_month_stats_completion_rate():
    stats = MonthStats(done=3, fired=4)
    assert stats.completion_rate == 75
    assert MonthStats().completion_rate == 0


def test_event_label_snoozed_extra():
    tz = ZoneInfo("Europe/Moscow")
    event = ReminderEvent(
        reminder_id=1,
        chat_id=1,
        user_telegram_id=1,
        reminder_text="test",
        event_kind=ReminderEventKind.SNOOZED.value,
        event_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
        extra='{"minutes": 15}',
    )
    label = _event_label(event, tz)
    assert "+15" in label or "15" in label


def test_format_day_journal_with_planned():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime(2026, 6, 1, 12, 0, tzinfo=tz)
    body = format_day_journal([], timezone="Europe/Moscow", day=now, active_count=2, planned_today=[])
    assert "Дневник" in body
    assert "2" in body


def test_format_month_stats():
    stats = MonthStats(done=1, fired=2, snoozed=1, created=3, deleted=1)
    text = format_month_stats(stats, month_label="Июнь 2026")
    assert "50%" in text
    assert "Июнь 2026" in text


@pytest.mark.asyncio
async def test_log_and_month_stats(patched_db):
    from bot.db.repository import create_reminder, get_or_create_user

    user = await get_or_create_user(patched_db, 88001, "Europe/Moscow")
    reminder = await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=88001,
        created_by_telegram_id=88001,
        timezone="Europe/Moscow",
        text="hist test",
        kind="once",
        next_run_at=None,
    )
    now = datetime.now(ZoneInfo("Europe/Moscow"))
    await log_reminder_event(
        patched_db,
        reminder=reminder,
        chat_id=88001,
        user_telegram_id=88001,
        text="hist test",
        kind=ReminderEventKind.DONE,
        event_at=now,
    )
    stats = await get_month_stats(
        patched_db, 88001, day=now, timezone="Europe/Moscow", user_telegram_id=88001
    )
    assert stats.done >= 1
