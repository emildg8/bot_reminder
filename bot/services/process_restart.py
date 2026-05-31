"""Перезапуск процесса — совместимо с Wispbyte/Pterodactyl (без os.execv)."""

from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)

# 0 — панель перезапускает startup-команду (pip install && python -m bot.main)
RESTART_EXIT_CODE = 0


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(0x100000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def exit_for_restart(reason: str) -> None:
    """Чистый выход — панель поднимет новый процесс с обновлённым кодом."""
    logger.info("%s — exit %s for panel restart", reason, RESTART_EXIT_CODE)
    sys.exit(RESTART_EXIT_CODE)
