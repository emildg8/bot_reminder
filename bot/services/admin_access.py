"""Права администратора бота и режим admin / user."""

from __future__ import annotations

from bot.config import settings

_admin_tools_cache: dict[int, bool] = {}


def is_admin_listed(user_id: int) -> bool:
    return bool(settings.admin_telegram_ids) and user_id in settings.admin_telegram_ids


def is_bot_admin(user_id: int) -> bool:
    """Админ-команды и Pro-bypass — только в режиме администратора."""
    if not is_admin_listed(user_id):
        return False
    return _admin_tools_cache.get(user_id, True)


def admin_tools_cached(user_id: int) -> bool | None:
    if user_id in _admin_tools_cache:
        return _admin_tools_cache[user_id]
    return None


def set_admin_tools_cached(user_id: int, enabled: bool) -> None:
    _admin_tools_cache[user_id] = enabled


async def get_admin_tools_enabled(session, telegram_id: int) -> bool:
    if not is_admin_listed(telegram_id):
        return False
    cached = admin_tools_cached(telegram_id)
    if cached is not None:
        return cached
    from bot.db.repository import get_user_by_telegram_id

    user = await get_user_by_telegram_id(session, telegram_id)
    enabled = True if user is None else user.admin_tools_enabled
    set_admin_tools_cached(telegram_id, enabled)
    return enabled


async def set_admin_tools_enabled(session, telegram_id: int, enabled: bool) -> None:
    from bot.db.repository import get_or_create_user

    user = await get_or_create_user(session, telegram_id, settings.default_timezone)
    user.admin_tools_enabled = enabled
    await session.commit()
    set_admin_tools_cached(telegram_id, enabled)


async def load_admin_tools_cache() -> None:
    if not settings.admin_telegram_ids:
        return
    from bot.db.repository import async_session

    async with async_session() as session:
        for admin_id in settings.admin_telegram_ids:
            await get_admin_tools_enabled(session, admin_id)


def format_bot_admin_denied(user_id: int) -> str:
    """Сообщение при попытке админ-команды без прав."""
    if is_admin_listed(user_id) and not is_bot_admin(user_id):
        return (
            "👤 Сейчас включён <b>режим пользователя</b> — админ-команды скрыты.\n\n"
            "Вернуть инструменты: <code>/adminmode admin</code> или кнопка в /adminmode"
        )
    return "Команда доступна только администраторам бота."
