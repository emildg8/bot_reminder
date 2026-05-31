from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from bot.services.reminder_utils import ensure_future_run_at, local_run_at


def test_local_run_at_naive_moscow_not_utc():
    """SQLite отдаёт naive 04:10 — это Москва, не UTC сервера."""
    naive = datetime(2026, 5, 31, 4, 10, 0)
    local = local_run_at(naive, "Europe/Moscow")
    assert local is not None
    assert local.tzinfo == ZoneInfo("Europe/Moscow")
    assert local.hour == 4
    assert local.minute == 10
    assert local.astimezone(UTC).hour == 1


def test_ensure_future_run_at_from_naive_moscow():
    future = datetime.now(ZoneInfo("Europe/Moscow")) + timedelta(hours=2)
    naive = future.replace(tzinfo=None)
    utc = ensure_future_run_at(naive, "Europe/Moscow", min_seconds=3)
    assert utc.tzinfo == ZoneInfo("UTC")
    moscow = utc.astimezone(ZoneInfo("Europe/Moscow"))
    assert moscow.hour == future.hour
    assert moscow.minute == future.minute


def test_ensure_future_run_at_past_becomes_soon():
    past = datetime.now(ZoneInfo("Europe/Moscow")) - timedelta(hours=1)
    utc = ensure_future_run_at(past, "Europe/Moscow", min_seconds=5)
    assert (utc - datetime.now(UTC)).total_seconds() <= 10
