import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from bot.services.heartbeat import HEARTBEAT_MAX_AGE_SECONDS, write_heartbeat


def test_write_heartbeat_creates_file(tmp_path, monkeypatch):
    hb = tmp_path / "heartbeat.json"
    monkeypatch.setattr("bot.services.heartbeat.DATA_DIR", tmp_path)
    monkeypatch.setattr("bot.services.heartbeat.HEARTBEAT_PATH", hb)

    write_heartbeat(scheduler_running=True)

    data = json.loads(hb.read_text(encoding="utf-8"))
    assert data["scheduler"] is True
    assert data["pid"] == os.getpid()
    assert datetime.fromisoformat(data["ts"]).tzinfo is not None


def test_healthcheck_passes_with_fresh_heartbeat(tmp_path, monkeypatch):
    hb = tmp_path / "heartbeat.json"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "scheduler": True,
    }
    hb.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    from scripts.healthcheck import main

    assert main() == 0


def test_healthcheck_fails_on_stale_heartbeat(tmp_path, monkeypatch):
    hb = tmp_path / "heartbeat.json"
    stale = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_MAX_AGE_SECONDS + 10)
    payload = {"ts": stale.isoformat(), "pid": os.getpid(), "scheduler": True}
    hb.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    from scripts.healthcheck import main

    assert main() == 1


def test_healthcheck_fails_when_scheduler_stopped(tmp_path, monkeypatch):
    hb = tmp_path / "heartbeat.json"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "scheduler": False,
    }
    hb.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    from scripts.healthcheck import main

    assert main() == 1


def test_healthcheck_fails_on_dead_pid(tmp_path, monkeypatch):
    hb = tmp_path / "heartbeat.json"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pid": 999999999,
        "scheduler": True,
    }
    hb.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    from scripts.healthcheck import main

    with patch("scripts.healthcheck.os.kill", side_effect=OSError):
        assert main() == 1
