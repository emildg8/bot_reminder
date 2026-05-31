from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.services.nlp.relative_delay import apply_relative_delay
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import compute_next_run


def test_llm_relative_delay_from_phrase():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    run_at = now + timedelta(hours=2)
    parsed = ParsedReminder(text="обед", kind="once", run_at=run_at)
    result = apply_relative_delay(parsed, "через 2 часа обед", "Europe/Moscow")
    assert result.delay_seconds is not None
    assert 7000 <= result.delay_seconds <= 7300


def test_llm_absolute_date_no_delay():
    tz = ZoneInfo("Europe/Moscow")
    run_at = datetime(2030, 6, 15, 14, 0, tzinfo=tz)
    parsed = ParsedReminder(text="созвон", kind="once", run_at=run_at)
    result = apply_relative_delay(parsed, "15 июня в 14:00 созвон", "Europe/Moscow")
    assert result.delay_seconds is None


def test_llm_delay_recomputed_at_confirm():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    run_at = now + timedelta(minutes=30)
    parsed = apply_relative_delay(
        ParsedReminder(text="таблетки", kind="once", run_at=run_at),
        "через 30 минут таблетки",
        "Europe/Moscow",
    )
    before = datetime.now(tz)
    next_run = compute_next_run(parsed, "Europe/Moscow")
    after = datetime.now(tz)
    assert before + timedelta(minutes=25) <= next_run <= after + timedelta(minutes=35)
