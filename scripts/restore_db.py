#!/usr/bin/env python3
"""Восстановление SQLite из бэкапа.

Usage:
  python scripts/restore_db.py                    # последний бэкап
  python scripts/restore_db.py path/to/file.db    # конкретный файл
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot.services.backup import _db_path  # noqa: E402


def main() -> None:
    db = _db_path()
    backup_dir = ROOT / "data" / "backups"

    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        backups = sorted(backup_dir.glob("reminders_*.db"), key=lambda p: p.stat().st_mtime)
        if not backups:
            print(f"Нет бэкапов в {backup_dir}")
            sys.exit(1)
        src = backups[-1]

    if not src.exists():
        print(f"Файл не найден: {src}")
        sys.exit(1)

    if db.exists():
        safety = db.with_suffix(".db.before_restore")
        shutil.copy2(db, safety)
        print(f"Текущая БД сохранена: {safety}")

    db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, db)
    print(f"Восстановлено из {src} -> {db}")


if __name__ == "__main__":
    main()
