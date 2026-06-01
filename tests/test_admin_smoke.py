"""Smoke: admin panel + audit + broadcast draft (CI e2e subset)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.handlers.admin import cmd_admin_panel, cmd_adminlog, cmd_broadcast
from bot.services.admin_access import set_admin_tools_cached
from bot.services.admin_panel import pop_pending_broadcast


@pytest.mark.asyncio
async def test_admin_smoke_panel_log_broadcast(monkeypatch, patched_db):
    admin_id = 88010
    monkeypatch.setattr("bot.services.admin_access.settings.admin_telegram_ids", [admin_id])
    set_admin_tools_cached(admin_id, True)

    message = MagicMock()
    message.from_user.id = admin_id
    message.answer = AsyncMock()

    await cmd_admin_panel(message)
    assert "Панель администратора" in message.answer.await_args[0][0]

    message.text = "/broadcast smoke test"
    await cmd_broadcast(message, MagicMock())
    pending = await pop_pending_broadcast(admin_id)
    assert pending is not None
    assert pending.text == "smoke test"

    await cmd_adminlog(message)
    bodies = [c[0][0] for c in message.answer.await_args_list]
    assert any("Журнал" in b for b in bodies)
