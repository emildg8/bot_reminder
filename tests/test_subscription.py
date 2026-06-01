import pytest

from bot.config import settings
from bot.db.repository import create_reminder, get_or_create_user, set_user_pro
from bot.services.subscription import can_add_reminder, format_limit_reached, is_pro_user
from tests.db_helpers import patched_db


@pytest.mark.asyncio
async def test_free_limit_blocks_at_threshold(patched_db):
    user_id = 9600
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    limit = settings.free_active_limit

    for i in range(limit):
        await create_reminder(
            patched_db,
            user_id=user.id,
            chat_id=user_id,
            created_by_telegram_id=user_id,
            timezone="Europe/Moscow",
            text=f"task {i}",
            kind="once",
            next_run_at=None,
        )

    allowed, current, lim = await can_add_reminder(patched_db, user_id)
    assert allowed is False
    assert current == limit
    assert lim == limit
    assert "лимит" in format_limit_reached(current, lim).lower()


@pytest.mark.asyncio
async def test_pro_user_unlimited(patched_db):
    user_id = 9601
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    await set_user_pro(patched_db, user_id, is_pro=True)
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")

    assert is_pro_user(user, user_id) is True
    allowed, _, limit = await can_add_reminder(patched_db, user_id)
    assert allowed is True
    assert limit == 0
