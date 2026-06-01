import pytest
from unittest.mock import AsyncMock

from bot.db.repository import create_reminder, get_or_create_user, get_reminder
from bot.services.reminder_delete import delete_owned_reminder
async def _seed(session, owner: int, creator: int | None = None, text: str = "удалить"):
    user = await get_or_create_user(session, owner, "Europe/Moscow")
    creator = creator if creator is not None else owner
    return await create_reminder(
        session,
        user_id=user.id,
        chat_id=-100600,
        created_by_telegram_id=creator,
        timezone="Europe/Moscow",
        text=text,
        kind="once",
        next_run_at=None,
    )


@pytest.mark.asyncio
async def test_delete_owned_reminder_success(patched_db, monkeypatch):
    user_id = 9500
    reminder = await _seed(patched_db, user_id)
    bot = AsyncMock()
    monkeypatch.setattr(
        "bot.services.reminder_delete.teardown_reminder_schedule",
        AsyncMock(),
    )
    monkeypatch.setattr(
        "bot.services.reminder_delete.log_reminder_event",
        AsyncMock(),
    )

    err, deleted = await delete_owned_reminder(bot, patched_db, reminder.id, user_id)

    assert err is None
    assert deleted is not None
    refreshed = await get_reminder(patched_db, reminder.id)
    assert refreshed is not None
    assert refreshed.is_active is False


@pytest.mark.asyncio
async def test_delete_owned_reminder_denied_for_other_user(patched_db):
    reminder = await _seed(patched_db, owner=9501, creator=9501)
    bot = AsyncMock()

    err, deleted = await delete_owned_reminder(bot, patched_db, reminder.id, 99999)

    assert "свои" in err.lower()
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_owned_reminder_not_found(patched_db):
    bot = AsyncMock()
    err, deleted = await delete_owned_reminder(bot, patched_db, 999999, 9502)
    assert "не найдено" in err.lower()
    assert deleted is None
