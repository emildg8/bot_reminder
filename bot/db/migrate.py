"""Alembic migrations — SQLite и PostgreSQL."""

from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from bot.config import BASE_DIR, settings

logger = logging.getLogger(__name__)

ALEMBIC_INI = BASE_DIR / "alembic.ini"


def sync_database_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
    return url


def is_sqlite_url(url: str | None = None) -> bool:
    url = url or settings.database_url
    return url.startswith("sqlite")


def is_postgres_url(url: str | None = None) -> bool:
    url = url or settings.database_url
    return url.startswith("postgresql")


def _alembic_config() -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", sync_database_url(settings.database_url))
    return cfg


def _has_app_tables(engine) -> bool:
    inspector = inspect(engine)
    return inspector.has_table("users")


def _has_alembic_version(engine) -> bool:
    inspector = inspect(engine)
    return inspector.has_table("alembic_version")


def _sqlite_legacy_backfill(engine) -> None:
    """Одноразовое заполнение NULL-колонок на старых SQLite-базах."""
    if not is_sqlite_url():
        return
    with engine.begin() as conn:
        inspector = inspect(conn)
        if not inspector.has_table("reminders"):
            return
        cols = {c["name"] for c in inspector.get_columns("reminders")}
        if "chat_id" not in cols:
            return
        conn.execute(
            text(
                """
                UPDATE reminders
                SET chat_id = (SELECT telegram_id FROM users WHERE users.id = reminders.user_id)
                WHERE chat_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE reminders
                SET created_by_telegram_id = (
                    SELECT telegram_id FROM users WHERE users.id = reminders.user_id
                )
                WHERE created_by_telegram_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE reminders
                SET timezone = (SELECT timezone FROM users WHERE users.id = reminders.user_id)
                WHERE timezone IS NULL
                """
            )
        )


def upgrade_database() -> None:
    sync_url = sync_database_url(settings.database_url)
    engine = create_engine(sync_url)

    cfg = _alembic_config()
    if _has_app_tables(engine) and not _has_alembic_version(engine):
        logger.info("Existing database without alembic_version — stamping head")
        command.stamp(cfg, "head")
        _sqlite_legacy_backfill(engine)
        engine.dispose()
        return

    command.upgrade(cfg, "head")
    _sqlite_legacy_backfill(engine)
    engine.dispose()
    logger.info("Database migrations applied (head)")


async def init_db_migrations() -> None:
    import asyncio

    await asyncio.to_thread(upgrade_database)
