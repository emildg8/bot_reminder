from datetime import datetime, timedelta, timezone

from bot.services.scheduler import compute_restore_run_at


def test_restore_jitter_increases():
    now = datetime(2026, 5, 30, 12, 0, tzinfo=timezone.utc)
    t0 = compute_restore_run_at(now, 0)
    t1 = compute_restore_run_at(now, 1)
    t10 = compute_restore_run_at(now, 10)
    assert t0 == now
    assert t1 == now + timedelta(seconds=3)
    assert t10 == now + timedelta(seconds=30)


def test_restore_jitter_capped():
    now = datetime(2026, 5, 30, 12, 0, tzinfo=timezone.utc)
    t100 = compute_restore_run_at(now, 100)
    assert t100 == now + timedelta(seconds=120)
