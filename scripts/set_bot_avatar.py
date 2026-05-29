"""Установка аватарки бота через Telegram Bot API."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, InputProfilePhotoStatic
from aiogram.utils.token import TokenValidationError, validate_token

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_AVATAR = ASSETS_DIR / "bot_avatar.jpg"
TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")


def is_plausible_bot_token(token: str) -> bool:
    token = token.strip()
    if not TOKEN_PATTERN.match(token):
        return False
    try:
        validate_token(token)
        return True
    except TokenValidationError:
        return False


async def set_bot_avatar(bot: Bot, avatar_path: Path | None = None) -> bool:
    """Загружает JPG-аватарку бота. Возвращает True при успехе."""
    path = avatar_path or DEFAULT_AVATAR
    if not path.exists():
        raise FileNotFoundError(f"Avatar not found: {path}")

    photo = InputProfilePhotoStatic(photo=FSInputFile(path))
    result = await bot.set_my_profile_photo(photo=photo)
    logger.info("Bot avatar updated from %s", path)
    return result


async def verify_bot_has_avatar(bot: Bot) -> bool:
    """Проверяет, что у бота есть хотя бы одно фото профиля."""
    me = await bot.get_me()
    photos = await bot.get_user_profile_photos(user_id=me.id, limit=1)
    return photos.total_count > 0


async def run_set_and_verify(token: str, avatar_path: Path | None = None) -> None:
    if not is_plausible_bot_token(token):
        raise ValueError("BOT_TOKEN missing or invalid")

    bot = Bot(token=token)
    try:
        me = await bot.get_me()
        print(f"Bot: @{me.username} (id={me.id})")

        before = await verify_bot_has_avatar(bot)
        print(f"Avatar before: {'yes' if before else 'no'}")

        await set_bot_avatar(bot, avatar_path)
        print("set_my_profile_photo: OK")

        after = await verify_bot_has_avatar(bot)
        print(f"Avatar after: {'yes' if after else 'no'}")
        if not after:
            raise RuntimeError("Avatar not visible after upload")
        print("SUCCESS")
    finally:
        await bot.session.close()


def main() -> None:
    import os

    logging.basicConfig(level=logging.INFO)
    token = os.environ.get("BOT_TOKEN", "").strip()
    try:
        asyncio.run(run_set_and_verify(token))
    except ValueError as exc:
        raise SystemExit(f"{exc}. Set BOT_TOKEN in .env or environment.") from exc


if __name__ == "__main__":
    main()
