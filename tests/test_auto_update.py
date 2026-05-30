from unittest.mock import AsyncMock, patch

import httpx
import pytest

from bot.services.auto_update import fetch_remote_sha, should_restart_for_update
from bot.services.deploy_meta import read_deploy_sha, write_deploy_sha


def test_write_and_read_deploy_sha(tmp_path, monkeypatch):
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", tmp_path / "deploy_sha.txt")
    write_deploy_sha("abc123def456")
    assert read_deploy_sha() == "abc123def456"


@pytest.mark.asyncio
async def test_fetch_remote_sha_success():
    response = httpx.Response(200, json={"sha": "deadbeef" * 5})
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("bot.services.auto_update.httpx.AsyncClient", return_value=mock_client):
        sha = await fetch_remote_sha()

    assert sha == "deadbeef" * 5


@pytest.mark.asyncio
async def test_should_restart_when_sha_differs(tmp_path, monkeypatch):
    sha_path = tmp_path / "deploy_sha.txt"
    sha_path.write_text("localsha1234567890", encoding="utf-8")
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", sha_path)
    monkeypatch.setattr("bot.services.auto_update.read_deploy_sha", read_deploy_sha)

    with patch(
        "bot.services.auto_update.fetch_remote_sha",
        new=AsyncMock(return_value="remotesha123456789"),
    ):
        need, local, remote = await should_restart_for_update()

    assert need is True
    assert local == "localsha1234567890"
    assert remote == "remotesha123456789"


@pytest.mark.asyncio
async def test_should_not_restart_when_sha_matches(tmp_path, monkeypatch):
    sha_path = tmp_path / "deploy_sha.txt"
    sha_path.write_text("samecommitsha12345", encoding="utf-8")
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", sha_path)
    monkeypatch.setattr("bot.services.auto_update.read_deploy_sha", read_deploy_sha)

    with patch(
        "bot.services.auto_update.fetch_remote_sha",
        new=AsyncMock(return_value="samecommitsha12345"),
    ):
        need, _, remote = await should_restart_for_update()

    assert need is False
    assert remote == "samecommitsha12345"


@pytest.mark.asyncio
async def test_should_not_restart_when_disabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.auto_update_enabled", False)
    need, local, remote = await should_restart_for_update()
    assert need is False
    assert local is None
    assert remote is None
