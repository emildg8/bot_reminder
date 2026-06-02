"""Строка deploy sha для ops-команд."""

from bot.services.auto_update import fetch_remote_sha
from bot.services.deploy_meta import read_deploy_sha


def format_startup_admin_message(version: str, *, privacy_warn: str | None = None) -> str:
    sha = read_deploy_sha()
    sha_label = f" · <code>{sha[:7]}</code>" if sha else ""
    msg = f"✅ Бот запущен · v{version}{sha_label}"
    if privacy_warn:
        msg += f"\n\n{privacy_warn}"
    return msg


async def format_deploy_line() -> str:
    local_sha = read_deploy_sha()
    remote_sha = await fetch_remote_sha()
    if not local_sha and not remote_sha:
        return ""
    local_label = local_sha[:7] if local_sha else "—"
    remote_label = remote_sha[:7] if remote_sha else "—"
    return f"Deploy: <code>{local_label}</code> → GitHub <code>{remote_label}</code>\n"
