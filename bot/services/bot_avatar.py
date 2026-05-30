"""Загрузка аватарки бота в Telegram."""

from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.types import BufferedInputFile, InputProfilePhotoStatic
from PIL import Image

from bot.config import BASE_DIR

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
DEFAULT_AVATAR = ASSETS_DIR / "bot_avatar.jpg"
FALLBACK_AVATAR = ASSETS_DIR / "bot_avatar.png"
AVATAR_HASH_PATH = BASE_DIR / "data" / "avatar_hash.txt"
AVATAR_SIZE = 640


def _resolve_avatar_source() -> Path:
    if DEFAULT_AVATAR.exists():
        return DEFAULT_AVATAR
    if FALLBACK_AVATAR.exists():
        return FALLBACK_AVATAR
    raise FileNotFoundError(f"Avatar not found: {DEFAULT_AVATAR}")


def avatar_file_hash(path: Path | None = None) -> str:
    source = path or _resolve_avatar_source()
    return hashlib.sha256(source.read_bytes()).hexdigest()[:16]


def _read_stored_avatar_hash() -> str | None:
    if not AVATAR_HASH_PATH.exists():
        return None
    value = AVATAR_HASH_PATH.read_text(encoding="utf-8").strip()
    return value or None


def _write_stored_avatar_hash(digest: str) -> None:
    AVATAR_HASH_PATH.parent.mkdir(exist_ok=True)
    AVATAR_HASH_PATH.write_text(digest, encoding="utf-8")


def prepare_avatar_bytes(source_path: Path | None = None) -> bytes:
    """Центр-кроп в квадрат и ресайз до 640×640 — Telegram требует квадрат."""
    path = source_path or _resolve_avatar_source()
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        square = rgb.crop((left, top, left + side, top + side))
        if square.size != (AVATAR_SIZE, AVATAR_SIZE):
            square = square.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        square.save(buffer, format="JPEG", quality=92, optimize=True)
        return buffer.getvalue()


async def verify_bot_has_avatar(bot: Bot) -> bool:
    me = await bot.get_me()
    photos = await bot.get_user_profile_photos(user_id=me.id, limit=1)
    return photos.total_count > 0


async def set_bot_avatar(bot: Bot, avatar_path: Path | None = None) -> bool:
    path = avatar_path or _resolve_avatar_source()
    payload = prepare_avatar_bytes(path)
    photo = InputProfilePhotoStatic(
        photo=BufferedInputFile(payload, filename="bot_avatar.jpg"),
    )
    result = await bot.set_my_profile_photo(photo=photo)
    _write_stored_avatar_hash(avatar_file_hash(path))
    logger.info("Bot avatar updated from %s (%dx%d JPEG)", path, AVATAR_SIZE, AVATAR_SIZE)
    return result


async def ensure_bot_avatar(bot: Bot, *, force: bool = False) -> bool:
    """Загружает аватар, если его нет, force=True или файл изменился."""
    try:
        source = _resolve_avatar_source()
    except FileNotFoundError:
        logger.warning("Avatar file missing in %s", ASSETS_DIR)
        return False

    current_hash = avatar_file_hash(source)
    stored_hash = _read_stored_avatar_hash()
    needs_upload = force or stored_hash != current_hash

    if not needs_upload and await verify_bot_has_avatar(bot):
        logger.info("Bot avatar already set, skip upload")
        return True

    await set_bot_avatar(bot, source)
    if not await verify_bot_has_avatar(bot):
        raise RuntimeError("Avatar not visible after upload")
    return True
