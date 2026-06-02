#!/usr/bin/env python3
"""Проверка перед/после деплоя: версия, GitHub main, опционально Telegram."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.version import __version__  # noqa: E402

GITHUB_COMMITS = "https://api.github.com/repos/emildg8/bot_reminder/commits/main"
TIMEOUT = 30


def _get_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


def main() -> int:
    errors: list[str] = []
    print(f"version: v{__version__}")

    try:
        commit = _get_json(
            GITHUB_COMMITS,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "bot-reminder-check"},
        )
        print(f"github main: {(commit.get('sha') or '')[:7]}")
    except Exception as exc:
        errors.append(f"github: {exc}")

    token = os.environ.get("BOT_TOKEN", "").strip()
    if token:
        try:
            data = _get_json(f"https://api.telegram.org/bot{token}/getMe")
            if data.get("ok"):
                print(f"telegram: @{data['result'].get('username')} ok")
            else:
                errors.append(f"telegram getMe: {data}")
        except urllib.error.URLError as exc:
            errors.append(f"telegram: {exc}")
    else:
        print("telegram: skip (no BOT_TOKEN)")

    print("prod: /ping и /sysinfo в Telegram")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK check_deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
