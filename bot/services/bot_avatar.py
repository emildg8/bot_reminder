"""Загрузка аватарки бота в Telegram."""

from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InputProfilePhotoStatic

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
DEFAULT_AVATAR = ASSETS_DIR / "bot_avatar.jpg"


async def verify_bot_has_avatar(bot: Bot) -> bool:
    me = await bot.get_me()
    photos = await bot.get_user_profile_photos(user_id=me.id, limit=1)
    return photos.total_count > 0


async def set_bot_avatar(bot: Bot, avatar_path: Path | None = None) -> bool:
    path = avatar_path or DEFAULT_AVATAR
    if not path.exists():
        raise FileNotFoundError(f"Avatar not found: {path}")

    photo = InputProfilePhotoStatic(photo=FSInputFile(path))
    result = await bot.set_my_profile_photo(photo=photo)
    logger.info("Bot avatar updated from %s", path)
    return result


async def ensure_bot_avatar(bot: Bot, *, force: bool = False) -> bool:
    """Загружает аватар, если его нет или force=True."""
    if not DEFAULT_AVATAR.exists():
        logger.warning("Avatar file missing: %s", DEFAULT_AVATAR)
        return False

    if not force and await verify_bot_has_avatar(bot):
        logger.info("Bot avatar already set, skip upload")
        return True

    await set_bot_avatar(bot)
    if not await verify_bot_has_avatar(bot):
        raise RuntimeError("Avatar not visible after upload")
    return True
