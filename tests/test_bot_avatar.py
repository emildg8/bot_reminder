from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.services.bot_avatar import (
    DEFAULT_AVATAR,
    ensure_bot_avatar,
    set_bot_avatar,
    verify_bot_has_avatar,
)


@pytest.fixture
def avatar_path(tmp_path: Path) -> Path:
    path = tmp_path / "test.jpg"
    path.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
    return path


@pytest.mark.asyncio
async def test_set_bot_avatar(avatar_path: Path) -> None:
    bot = AsyncMock()
    bot.set_my_profile_photo = AsyncMock(return_value=True)

    result = await set_bot_avatar(bot, avatar_path)

    assert result is True
    bot.set_my_profile_photo.assert_awaited_once()


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

    assert await ensure_bot_avatar(bot) is True
    bot.set_my_profile_photo.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_uploads_when_missing(avatar_path: Path, monkeypatch) -> None:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=MagicMock(id=123))
    bot.get_user_profile_photos = AsyncMock(
        side_effect=[MagicMock(total_count=0), MagicMock(total_count=1)]
    )
    bot.set_my_profile_photo = AsyncMock(return_value=True)
    monkeypatch.setattr("bot.services.bot_avatar.DEFAULT_AVATAR", avatar_path)

    assert await ensure_bot_avatar(bot) is True
    bot.set_my_profile_photo.assert_awaited_once()


def test_default_avatar_exists_in_repo() -> None:
    assert DEFAULT_AVATAR.exists(), "Commit assets/bot_avatar.jpg to the repository"
