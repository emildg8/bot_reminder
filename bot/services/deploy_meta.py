"""Метаданные текущего деплоя (git sha)."""

from __future__ import annotations

import subprocess

from bot.config import BASE_DIR

DEPLOY_SHA_PATH = BASE_DIR / "data" / "deploy_sha.txt"


def read_deploy_sha() -> str | None:
    if not DEPLOY_SHA_PATH.exists():
        return None
    value = DEPLOY_SHA_PATH.read_text(encoding="utf-8").strip()
    return value or None


def write_deploy_sha(sha: str) -> None:
    DEPLOY_SHA_PATH.parent.mkdir(exist_ok=True)
    DEPLOY_SHA_PATH.write_text(sha.strip(), encoding="utf-8")


def record_deploy_sha_from_git() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=BASE_DIR,
    )
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    write_deploy_sha(sha)
    return sha
