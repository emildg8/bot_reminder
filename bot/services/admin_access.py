"""Проверка прав администратора бота."""

from bot.config import settings


def is_bot_admin(user_id: int) -> bool:
    return bool(settings.admin_telegram_ids) and user_id in settings.admin_telegram_ids
