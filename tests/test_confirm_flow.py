from datetime import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import Base
from bot.db.repository import get_active_chat_reminders, get_or_create_user
from bot.services.drafts import pop_draft, store_draft
from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_create import create_and_schedule_items


def _once_parsed(text: str = "тест") -> ParsedReminder:
    tz = ZoneInfo("Europe/Moscow")
    return ParsedReminder(
        text=text,
        kind="once",
        run_at=datetime(2030, 1, 15, 12, 0, tzinfo=tz),
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
async def test_draft_confirm_creates_reminder(db_session, monkeypatch):
    scheduled: list[tuple[int, datetime]] = []

    def fake_schedule(bot, reminder_id, next_run, *, timezone=None):
        scheduled.append((reminder_id, next_run))

    monkeypatch.setattr("bot.services.reminder_create.schedule_reminder", fake_schedule)
    monkeypatch.setattr(
        "bot.services.reminder_create.setup_channel_telegram_schedule",
        AsyncMock(),
    )
    monkeypatch.setattr("bot.services.reminder_create.log_reminder_event", AsyncMock())

    user_tg_id = 9001
    draft_id = store_draft(user_tg_id, _once_parsed("купить хлеб"))
    entry = pop_draft(draft_id, user_tg_id)
    assert entry is not None

    user = await get_or_create_user(db_session, user_tg_id, "Europe/Moscow")
    bot = AsyncMock()

    created = await create_and_schedule_items(
        db_session,
        bot,
        user_id=user.id,
        chat_id=user_tg_id,
        created_by_telegram_id=user_tg_id,
        timezone="Europe/Moscow",
        parsed_items=entry.parsed_items,
    )

    assert len(created) == 1
    reminder_id, when, text = created[0]
    assert text == "купить хлеб"
    assert when
    assert len(scheduled) == 1
    assert scheduled[0][0] == reminder_id

    active = await get_active_chat_reminders(db_session, user_tg_id)
    assert len(active) == 1
    assert active[0].text == "купить хлеб"


def test_pop_draft_wrong_user_returns_none():
    draft_id = store_draft(1, _once_parsed())
    assert pop_draft(draft_id, 2) is None
