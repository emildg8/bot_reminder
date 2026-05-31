from unittest.mock import AsyncMock

import pytest

from bot.services.health_monitor import run_health_monitor
from bot.services.scheduler import RepairStats


@pytest.mark.asyncio
async def test_health_monitor_notifies_on_repair(monkeypatch):
    monkeypatch.setattr("bot.services.health_monitor.settings.admin_telegram_ids", [1])
    snapshot = AsyncMock()
    snapshot.needs_repair = False
    repair = RepairStats(overdue_rescheduled=2, missing_job_fixed=1)

    async def fake_check(_bot):
        return snapshot, repair

    monkeypatch.setattr("bot.services.health_monitor.run_health_check", fake_check)

    bot = AsyncMock()
    await run_health_monitor(bot)
    bot.send_message.assert_awaited_once()
    assert "repair" in bot.send_message.await_args.args[1].lower()
