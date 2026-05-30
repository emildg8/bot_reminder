"""Heartbeat для healthcheck — файл обновляется пока бот жив."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
HEARTBEAT_PATH = DATA_DIR / "heartbeat.json"
HEARTBEAT_MAX_AGE_SECONDS = 120


def write_heartbeat(*, scheduler_running: bool) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "scheduler": scheduler_running,
    }
    HEARTBEAT_PATH.write_text(json.dumps(payload), encoding="utf-8")
