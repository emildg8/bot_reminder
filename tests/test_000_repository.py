from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import Base
from bot.db.repository import (
    create_reminder,
    deactivate_all_chat_reminders,
    deactivate_reminder,
    get_active_chat_reminders,
    get_or_create_chat,
    get_or_create_user,
    get_reminder,
    is_chat_paused,
    search_chat_reminders,
    set_chat_paused,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_or_create_user_idempotent(db_session):
    user1 = await get_or_create_user(db_session, 42, "Europe/Moscow")
    user2 = await get_or_create_user(db_session, 42, "Europe/Moscow")
    assert user1.id == user2.id
    assert user1.telegram_id == 42


@pytest.mark.asyncio
async def test_get_or_create_chat(db_session):
    chat = await get_or_create_chat(db_session, -100123, "Europe/Moscow")
    assert chat.chat_id == -100123
    same = await get_or_create_chat(db_session, -100123, "Asia/Yekaterinburg")
    assert same.id == chat.id


@pytest.mark.asyncio
async def test_create_and_search_reminders(db_session):
    user = await get_or_create_user(db_session, 1, "Europe/Moscow")
    tz = ZoneInfo("Europe/Moscow")
    run_at = datetime(2030, 6, 1, 10, 0, tzinfo=tz)

    reminder = await create_reminder(
        db_session,
        user_id=user.id,
        chat_id=1,
        created_by_telegram_id=1,
        timezone="Europe/Moscow",
        text="купить молоко",
        kind="once",
        next_run_at=run_at,
    )
    assert reminder.id is not None

    found = await get_reminder(db_session, reminder.id)
    assert found is not None
    assert found.text == "купить молоко"

    active = await get_active_chat_reminders(db_session, 1)
    assert len(active) == 1

    hits = await search_chat_reminders(db_session, 1, "молоко")
    assert len(hits) == 1
    assert hits[0].id == reminder.id


@pytest.mark.asyncio
async def test_deactivate_reminder(db_session):
    user = await get_or_create_user(db_session, 2, "Europe/Moscow")
    reminder = await create_reminder(
        db_session,
        user_id=user.id,
        chat_id=2,
        created_by_telegram_id=2,
        timezone="Europe/Moscow",
        text="ежедневная зарядка",
        kind="daily",
        daily_time=time(9, 0),
    )
    await deactivate_reminder(db_session, reminder)
    active = await get_active_chat_reminders(db_session, 2)
    assert active == []


@pytest.mark.asyncio
async def test_chat_pause(db_session):
    await set_chat_paused(db_session, -100, True)
    assert await is_chat_paused(db_session, -100) is True
    await set_chat_paused(db_session, -100, False)
    assert await is_chat_paused(db_session, -100) is False


@pytest.mark.asyncio
async def test_deactivate_all_chat_reminders(db_session):
    user = await get_or_create_user(db_session, 3, "Europe/Moscow")
    for text in ("a", "b", "c"):
        await create_reminder(
            db_session,
            user_id=user.id,
            chat_id=3,
            created_by_telegram_id=3,
            timezone="Europe/Moscow",
            text=text,
            kind="once",
        )
    count = await deactivate_all_chat_reminders(db_session, 3)
    assert count == 3
    assert await get_active_chat_reminders(db_session, 3) == []
