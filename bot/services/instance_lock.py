"""Lock-файл и перезапуск процесса."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from bot.services.process_restart import pid_alive

logger = logging.getLogger(__name__)


def acquire_instance_lock(data_dir: Path) -> Path:
    lock_path = data_dir / "bot.lock"
    if lock_path.exists():
        try:
            old_pid = int(lock_path.read_text(encoding="utf-8").strip())
        except ValueError:
            old_pid = 0
        if pid_alive(old_pid) and old_pid != os.getpid():
            logger.error("Another bot instance is running (pid %s) — exit", old_pid)
            sys.exit(1)
        if lock_path.exists():
            logger.warning("Removing stale lock (pid %s)", old_pid or "?")
            lock_path.unlink(missing_ok=True)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    return lock_path


def release_instance_lock(lock_path: Path) -> None:
    try:
        if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == str(os.getpid()):
            lock_path.unlink()
    except OSError as exc:
        logger.warning("Cannot remove lock file: %s", exc)
