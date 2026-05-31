import os
from unittest.mock import patch

from bot.services.instance_lock import acquire_instance_lock, release_instance_lock
from bot.services.process_restart import pid_alive


def test_pid_alive_current_process():
    assert pid_alive(os.getpid()) is True


def test_pid_alive_dead():
    assert pid_alive(99999999) is False


def test_stale_lock_removed(tmp_path, monkeypatch):
    lock_path = tmp_path / "bot.lock"
    lock_path.write_text("99999999", encoding="utf-8")
    monkeypatch.setattr("bot.services.instance_lock.pid_alive", lambda pid: False)
    acquired = acquire_instance_lock(tmp_path)
    assert acquired.read_text(encoding="utf-8") == str(os.getpid())
    release_instance_lock(acquired)
    assert not acquired.exists()


def test_live_lock_blocks_start(tmp_path, monkeypatch):
    lock_path = tmp_path / "bot.lock"
    lock_path.write_text("42", encoding="utf-8")
    monkeypatch.setattr("bot.services.instance_lock.pid_alive", lambda pid: pid == 42)
    with patch("bot.services.instance_lock.sys.exit") as exit_mock:
        acquire_instance_lock(tmp_path)
    exit_mock.assert_called_once_with(1)
