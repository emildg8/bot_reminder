"""Автообновление: проверка новых коммитов на GitHub и перезапуск."""

from __future__ import annotations

import logging

import httpx

from bot.config import settings
from bot.services.deploy_meta import read_deploy_sha

logger = logging.getLogger(__name__)


async def fetch_remote_sha() -> str | None:
    url = f"https://api.github.com/repos/{settings.github_repo}/commits/{settings.github_branch}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "bot-reminder-auto-update"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        logger.warning("GitHub API request failed: %s", exc)
        return None

    if response.status_code != 200:
        logger.warning("GitHub API status %s", response.status_code)
        return None

    sha = response.json().get("sha")
    return sha if isinstance(sha, str) and sha else None


async def should_restart_for_update() -> tuple[bool, str | None, str | None]:
    """Возвращает (нужен_рестарт, local_sha, remote_sha)."""
    if not settings.auto_update_enabled:
        return False, None, None

    local_sha = read_deploy_sha()
    if not local_sha:
        logger.debug("No local deploy sha — skip auto-update check")
        return False, None, None

    remote_sha = await fetch_remote_sha()
    if not remote_sha:
        return False, local_sha, None

    if remote_sha == local_sha:
        return False, local_sha, remote_sha

    logger.info(
        "New commit detected: local=%s remote=%s",
        local_sha[:7],
        remote_sha[:7],
    )
    return True, local_sha, remote_sha
