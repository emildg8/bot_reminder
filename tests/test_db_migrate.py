import pytest
from sqlalchemy import create_engine, inspect

from bot.db.migrate import is_postgres_url, is_sqlite_url, sync_database_url, upgrade_database


def test_sync_database_url_sqlite():
    assert sync_database_url("sqlite+aiosqlite:///./data/x.db") == "sqlite:///./data/x.db"


def test_sync_database_url_postgres():
    url = "postgresql+asyncpg://u:p@localhost/reminder"
    assert sync_database_url(url) == "postgresql+psycopg2://u:p@localhost/reminder"


def test_is_sqlite_url():
    assert is_sqlite_url("sqlite+aiosqlite:///./data/x.db") is True
    assert is_sqlite_url("postgresql+asyncpg://localhost/x") is False


def test_is_postgres_url():
    assert is_postgres_url("postgresql+asyncpg://localhost/x") is True


@pytest.mark.asyncio
async def test_upgrade_database_fresh_sqlite(tmp_path, monkeypatch):
    db_path = tmp_path / "fresh.db"
    url = f"sqlite+aiosqlite:///{db_path}"
    monkeypatch.setattr("bot.db.migrate.settings.database_url", url)
    monkeypatch.setattr("bot.config.settings.database_url", url)

    upgrade_database()

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    assert inspector.has_table("users")
    assert inspector.has_table("reminders")
    assert inspector.has_table("alembic_version")
    engine.dispose()
