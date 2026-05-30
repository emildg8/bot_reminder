from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.services.auto_update import (
    apply_git_update,
    apply_git_update_to_sha,
    consume_reexec_flag,
    fetch_remote_sha,
    request_process_reexec,
    should_restart_for_update,
)
from bot.services.deploy_meta import read_deploy_sha, write_deploy_sha


def test_write_and_read_deploy_sha(tmp_path, monkeypatch):
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", tmp_path / "deploy_sha.txt")
    write_deploy_sha("abc123def456")
    assert read_deploy_sha() == "abc123def456"


def test_reexec_flag():
    assert consume_reexec_flag() is False
    request_process_reexec()
    assert consume_reexec_flag() is True
    assert consume_reexec_flag() is False


@pytest.mark.asyncio
async def test_fetch_remote_sha_success():
    response = httpx.Response(200, json={"sha": "deadbeef" * 5})
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
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
async def test_should_bootstrap_sha_from_git(tmp_path, monkeypatch):
    git_dir = tmp_path / "repo"
    git_dir.mkdir()
    (git_dir / ".git").mkdir()
    sha_path = git_dir / "data" / "deploy_sha.txt"
    monkeypatch.setattr("bot.services.deploy_meta.BASE_DIR", git_dir)
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", sha_path)
    monkeypatch.setattr("bot.services.auto_update.BASE_DIR", git_dir)
    monkeypatch.setattr(
        "bot.services.auto_update.record_deploy_sha_from_git",
        lambda: "bootstrappedsha12345",
    )

    with patch(
        "bot.services.auto_update.fetch_remote_sha",
        new=AsyncMock(return_value="bootstrappedsha12345"),
    ):
        need, local, remote = await should_restart_for_update()

    assert need is False
    assert local == "bootstrappedsha12345"
    assert remote == "bootstrappedsha12345"


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


@pytest.mark.asyncio
async def test_apply_git_update_success(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "requirements.txt").write_text("", encoding="utf-8")
    monkeypatch.setattr("bot.services.auto_update.BASE_DIR", repo)
    monkeypatch.setattr(
        "bot.services.auto_update.record_deploy_sha_from_git",
        lambda: "newsha123456789012",
    )

    pull = MagicMock(returncode=0, stdout="Already up to date.", stderr="")
    pip = MagicMock(returncode=0, stdout="", stderr="")

    with (
        patch("bot.services.auto_update._run_git_pull", return_value=pull),
        patch("bot.services.auto_update._run_pip_install", return_value=pip),
    ):
        success, sha = await apply_git_update()

    assert success is True
    assert sha == "newsha123456789012"


@pytest.mark.asyncio
async def test_apply_git_update_fails_without_git(tmp_path, monkeypatch):
    monkeypatch.setattr("bot.services.auto_update.BASE_DIR", tmp_path)
    success, sha = await apply_git_update()
    assert success is False
    assert sha is None


@pytest.mark.asyncio
async def test_apply_git_update_to_sha_writes_remote_on_missing_rev(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    sha_path = repo / "data" / "deploy_sha.txt"
    monkeypatch.setattr("bot.services.deploy_meta.DEPLOY_SHA_PATH", sha_path)
    monkeypatch.setattr("bot.services.auto_update.BASE_DIR", repo)

    with patch(
        "bot.services.auto_update.apply_git_update",
        new=AsyncMock(return_value=(True, None)),
    ):
        success, sha = await apply_git_update_to_sha("remotecommitsha1234")

    assert success is True
    assert sha == "remotecommitsha1234"
    assert read_deploy_sha() == "remotecommitsha1234"
