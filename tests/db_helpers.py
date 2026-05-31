import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import bot.db.repository as repository
from bot.db.models import Base


class _SharedSessionFactory:
    """async_session() always returns the same in-memory session (for handler tests)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def __call__(self):
        return self

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest_asyncio.fixture
async def patched_db(monkeypatch) -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    session = session_factory()
    shared = _SharedSessionFactory(session)

    monkeypatch.setattr(repository, "engine", engine)
    monkeypatch.setattr(repository, "async_session", shared)
    monkeypatch.setattr("bot.handlers.callbacks.async_session", shared)

    yield session

    await session.close()
    await engine.dispose()
