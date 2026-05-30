#!/usr/bin/env python3
"""Docker healthcheck: процесс жив и heartbeat свежий."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_AGE_SECONDS = 120


def _data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "/app/data"))


def main() -> int:
    heartbeat_path = _data_dir() / "heartbeat.json"
    if not heartbeat_path.exists():
        return 1

    try:
        data = json.loads(heartbeat_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 1

    ts_raw = data.get("ts")
    if not ts_raw:
        return 1

    ts = datetime.fromisoformat(ts_raw)
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    if age > MAX_AGE_SECONDS:
        return 1

    if not data.get("scheduler"):
        return 1

    pid = data.get("pid")
    if not isinstance(pid, int):
        return 1

    try:
        os.kill(pid, 0)
    except OSError:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
