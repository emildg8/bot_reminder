"""Автообновление: проверка новых коммитов на GitHub, git pull и перезапуск."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bot.config import BASE_DIR, settings
from bot.services.deploy_meta import read_deploy_sha, record_deploy_sha_from_git, write_deploy_sha
from bot.services.process_restart import exit_for_restart

logger = logging.getLogger(__name__)

_reexec_after_update = False
_preserve_on_reclone = {"data", ".env"}


def consume_reexec_flag() -> bool:
    global _reexec_after_update
    if _reexec_after_update:
        _reexec_after_update = False
        return True
    return False


def request_process_reexec() -> None:
    global _reexec_after_update
    _reexec_after_update = True


async def fetch_remote_sha() -> str | None:
    import httpx

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


def _bootstrap_local_sha() -> str | None:
    local_sha = read_deploy_sha()
    if local_sha:
        return local_sha
    if not (BASE_DIR / ".git").is_dir():
        return None
    return record_deploy_sha_from_git()


async def should_restart_for_update() -> tuple[bool, str | None, str | None]:
    """Возвращает (нужен_рестарт, local_sha, remote_sha)."""
    if not settings.auto_update_enabled:
        return False, None, None

    local_sha = _bootstrap_local_sha()
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


def _run_git_pull() -> subprocess.CompletedProcess[str]:
    branch = settings.github_branch
    result = subprocess.run(
        ["git", "pull", "origin", branch, "--ff-only"],
        capture_output=True,
        text=True,
        check=False,
        cwd=BASE_DIR,
    )
    if result.returncode != 0:
        result = subprocess.run(
            ["git", "pull", "origin", branch],
            capture_output=True,
            text=True,
            check=False,
            cwd=BASE_DIR,
        )
    return result


def _run_pip_install() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
        capture_output=True,
        text=True,
        check=False,
        cwd=BASE_DIR,
    )


def _reclone_repo() -> bool:
    """Полное обновление как start.sh, если git pull недоступен."""
    branch = settings.github_branch
    repo = settings.github_repo
    tmp = Path(tempfile.mkdtemp(prefix="bot_reminder_update_"))
    try:
        clone = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "-b",
                branch,
                f"https://github.com/{repo}.git",
                str(tmp),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if clone.returncode != 0:
            logger.warning(
                "git clone failed: %s",
                (clone.stderr or clone.stdout).strip(),
            )
            return False

        for item in tmp.iterdir():
            if item.name in _preserve_on_reclone:
                continue
            dest = BASE_DIR / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def apply_git_update() -> tuple[bool, str | None]:
    """git pull (+ reclone fallback) + pip install. Возвращает (успех, новый sha)."""
    pulled = False
    if (BASE_DIR / ".git").is_dir():
        pull = await asyncio.to_thread(_run_git_pull)
        if pull.returncode == 0:
            pulled = True
        else:
            logger.warning("git pull failed: %s", (pull.stderr or pull.stdout).strip())
    else:
        logger.warning("No .git directory — trying fresh clone")

    if not pulled:
        cloned = await asyncio.to_thread(_reclone_repo)
        if not cloned:
            return False, None

    pip = await asyncio.to_thread(_run_pip_install)
    if pip.returncode != 0:
        logger.warning("pip install failed: %s", (pip.stderr or pip.stdout).strip())

    new_sha = record_deploy_sha_from_git()
    if not new_sha:
        logger.warning("Could not record deploy sha after update")
        return False, None

    logger.info("Auto-update applied: %s", new_sha[:7])
    return True, new_sha


async def force_update() -> tuple[bool, str, str | None]:
    """Принудительное обновление. Возвращает (успех, сообщение, новый sha)."""
    local_sha = _bootstrap_local_sha()
    remote_sha = await fetch_remote_sha()
    if not remote_sha:
        return False, "❌ Не удалось проверить GitHub. Попробуй Restart в панели Wispbyte.", None

    if local_sha and remote_sha == local_sha:
        from bot.version import __version__

        return True, f"✅ Уже актуально · v{__version__} · <code>{local_sha[:7]}</code>", local_sha

    success, new_sha = await apply_git_update_to_sha(remote_sha)
    if not success or not new_sha:
        return (
            False,
            "❌ Не удалось скачать обновление. Сделай <b>Restart</b> сервера в панели Wispbyte.",
            None,
        )

    return (
        True,
        f"✅ Обновлено до <code>{new_sha[:7]}</code> — перезапуск…",
        new_sha,
    )


_shutdown_dispatcher = None


def register_shutdown_dispatcher(dp) -> None:
    global _shutdown_dispatcher
    _shutdown_dispatcher = dp


async def restart_bot_after_update(delay_seconds: float = 1.5) -> None:
    """Корректный перезапуск: stop polling → exit (панель поднимет процесс заново)."""
    await asyncio.sleep(delay_seconds)
    request_process_reexec()
    if _shutdown_dispatcher is not None:
        try:
            await _shutdown_dispatcher.stop_polling()
        except RuntimeError as exc:
            if "not started" not in str(exc).lower():
                raise
        return
    exit_for_restart("Manual restart without dispatcher")


def schedule_process_restart(delay_seconds: float = 1.5) -> None:
    asyncio.get_running_loop().create_task(restart_bot_after_update(delay_seconds))


async def apply_git_update_to_sha(remote_sha: str) -> tuple[bool, str | None]:
    """Обновляет код и фиксирует sha (fallback если git rev-parse недоступен)."""
    success, new_sha = await apply_git_update()
    if success and new_sha:
        return True, new_sha
    if success:
        write_deploy_sha(remote_sha)
        return True, remote_sha
    return False, None
