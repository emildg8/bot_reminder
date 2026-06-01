from bot.services.admin_access import is_bot_admin
from bot.services.health_status import HealthSnapshot, format_health_message
from bot.services.scheduler import RepairStats


def test_is_bot_admin(monkeypatch):
    from bot.services.admin_access import set_admin_tools_cached

    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    set_admin_tools_cached(42, True)
    assert is_bot_admin(42) is True
    assert is_bot_admin(1) is False


def test_is_bot_admin_user_mode(monkeypatch):
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [42])
    from bot.services.admin_access import set_admin_tools_cached

    set_admin_tools_cached(42, False)
    assert is_bot_admin(42) is False


def test_health_needs_repair():
    ok = HealthSnapshot(1, 5, 5, 0, 5, 0, True)
    assert ok.needs_repair is False

    overdue = HealthSnapshot(1, 5, 5, 2, 5, 0, True)
    assert overdue.needs_repair is True

    drift = HealthSnapshot(1, 5, 5, 0, 2, 5, True)
    assert drift.needs_repair is True


def test_format_health_with_repair():
    snapshot = HealthSnapshot(10, 3, 3, 0, 3, 0, True)
    repair = RepairStats(overdue_rescheduled=2, missing_job_fixed=1)
    text = format_health_message(
        snapshot,
        version="3.8.0",
        uptime="1 ч",
        deploy_line="",
        repair=repair,
    )
    assert "Перепланировано" in text
    assert "2" in text
