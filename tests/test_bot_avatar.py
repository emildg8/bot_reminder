import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from bot.services.bot_avatar import (
    AVATAR_SIZE,
    DEFAULT_AVATAR,
    avatar_file_hash,
    ensure_bot_avatar,
    prepare_avatar_bytes,
    set_bot_avatar,
    verify_bot_has_avatar,
)


def _make_landscape_png(path: Path, *, width: int = 900, height: int = 600) -> None:
    image = Image.new("RGB", (width, height), color=(120, 180, 240))
    # white circle in center — stays round after square crop
    cx, cy = width // 2, height // 2
    radius = min(width, height) // 4
    for x in range(width):
        for y in range(height):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
                image.putpixel((x, y), (255, 255, 255))
    image.save(path, format="PNG")


@pytest.fixture
def avatar_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.png"
    _make_landscape_png(path)
    return path


def test_prepare_avatar_bytes_makes_square_jpeg(avatar_path: Path) -> None:
    payload = prepare_avatar_bytes(avatar_path)
    with Image.open(io.BytesIO(payload)) as image:
        assert image.size == (AVATAR_SIZE, AVATAR_SIZE)
        assert image.format == "JPEG"


def test_avatar_file_hash_stable(avatar_path: Path) -> None:
    assert avatar_file_hash(avatar_path) == avatar_file_hash(avatar_path)


@pytest.mark.asyncio
async def test_set_bot_avatar(avatar_path: Path) -> None:
    bot = AsyncMock()
    bot.set_my_profile_photo = AsyncMock(return_value=True)

    with patch("bot.services.bot_avatar._write_stored_avatar_hash"):
        result = await set_bot_avatar(bot, avatar_path)

    assert result is True
    bot.set_my_profile_photo.assert_awaited_once()
    call_kwargs = bot.set_my_profile_photo.await_args.kwargs
    assert call_kwargs["photo"].photo.filename == "bot_avatar.jpg"


@pytest.mark.asyncio
async def test_set_bot_avatar_missing_file() -> None:
    bot = AsyncMock()
    with pytest.raises(FileNotFoundError):
        await set_bot_avatar(bot, Path("/nonexistent/avatar.jpg"))


@pytest.mark.asyncio
async def test_verify_bot_has_avatar_true() -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(return_value=MagicMock(total_count=1))

    assert await verify_bot_has_avatar(bot) is True


@pytest.mark.asyncio
async def test_verify_bot_has_avatar_false() -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(return_value=MagicMock(total_count=0))

    assert await verify_bot_has_avatar(bot) is False


@pytest.mark.asyncio
async def test_ensure_skips_when_avatar_exists(avatar_path: Path, monkeypatch) -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(return_value=MagicMock(total_count=1))
    monkeypatch.setattr("bot.services.bot_avatar.DEFAULT_AVATAR", avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar.FALLBACK_AVATAR", avatar_path)
    digest = avatar_file_hash(avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar._read_stored_avatar_hash", lambda: digest)

    assert await ensure_bot_avatar(bot) is True
    bot.set_my_profile_photo.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_uploads_when_missing(avatar_path: Path, monkeypatch) -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(return_value=MagicMock(total_count=1))
    bot.set_my_profile_photo = AsyncMock(return_value=True)
    monkeypatch.setattr("bot.services.bot_avatar.DEFAULT_AVATAR", avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar.FALLBACK_AVATAR", avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar._read_stored_avatar_hash", lambda: None)

    assert await ensure_bot_avatar(bot) is True
    bot.set_my_profile_photo.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_reuploads_when_file_changed(avatar_path: Path, monkeypatch) -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(
        side_effect=[MagicMock(total_count=1), MagicMock(total_count=1)]
    )
    bot.set_my_profile_photo = AsyncMock(return_value=True)
    monkeypatch.setattr("bot.services.bot_avatar.DEFAULT_AVATAR", avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar.FALLBACK_AVATAR", avatar_path)
    monkeypatch.setattr("bot.services.bot_avatar._read_stored_avatar_hash", lambda: "oldhash123456789")

    assert await ensure_bot_avatar(bot) is True
    bot.set_my_profile_photo.assert_awaited_once()


def test_default_avatar_exists_in_repo() -> None:
    assert DEFAULT_AVATAR.exists(), "Commit assets/bot_avatar.jpg to the repository"
    with Image.open(DEFAULT_AVATAR) as image:
        assert image.size[0] == image.size[1], "Avatar must be square"
