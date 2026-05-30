"""Автоматический backup SQLite."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bot.config import BASE_DIR, settings

logger = logging.getLogger(__name__)


def _db_path() -> Path:
    url = settings.database_url
    if url.startswith("sqlite"):
        raw = url.split("///", 1)[-1]
        path = Path(raw)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path
    raise ValueError(f"Backup supported only for SQLite, got: {url}")


def backup_database() -> Path | None:
    src = _db_path()
    if not src.exists():
        logger.warning("Database file not found: %s", src)
        return None

    backup_dir = BASE_DIR / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"reminders_{ts}.db"

    try:
        with sqlite3.connect(str(src), timeout=30) as src_conn:
            with sqlite3.connect(str(dest)) as dest_conn:
                src_conn.backup(dest_conn)
    except Exception as exc:
        logger.exception("Database backup failed: %s", exc)
        dest.unlink(missing_ok=True)
        return None

    logger.info("Database backup: %s", dest)

    backups = sorted(backup_dir.glob("reminders_*.db"), key=lambda p: p.stat().st_mtime)
    keep = settings.db_backup_keep
    for old in backups[:-keep]:
        old.unlink(missing_ok=True)
        logger.debug("Removed old backup: %s", old)

    return dest
