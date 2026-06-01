import pytest

from bot.services.admin_audit import format_admin_log, log_admin_action


@pytest.mark.asyncio
async def test_admin_log_persisted(patched_db):
    for i in range(5):
        await log_admin_action(1, f"action-{i}")
    text = await format_admin_log(limit=3)
    assert "action-4" in text
    assert "action-0" not in text
    assert "Журнал" in text


@pytest.mark.asyncio
async def test_admin_log_empty(patched_db):
    text = await format_admin_log()
    assert "Пока пуст" in text
