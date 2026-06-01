"""Smoke tests — импорты и wiring, которые pytest-cov не ловит."""

import importlib


def test_main_module_imports():
    importlib.import_module("bot.main")


def test_startup_helpers_importable():
    from bot.services.heartbeat import write_heartbeat
    from bot.services.process_restart import exit_for_restart

    assert callable(write_heartbeat)
    assert callable(exit_for_restart)


def test_admin_runtime_helpers_importable():
    from bot.services.runtime import format_uptime

    assert format_uptime(3661).startswith("1 ч")
