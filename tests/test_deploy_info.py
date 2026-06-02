from unittest.mock import AsyncMock

import pytest

from bot.services.deploy_info import format_deploy_line, format_startup_admin_message


@pytest.mark.asyncio
async def test_format_deploy_line_empty(monkeypatch):
    monkeypatch.setattr("bot.services.deploy_info.read_deploy_sha", lambda: None)
    monkeypatch.setattr(
        "bot.services.deploy_info.fetch_remote_sha",
        AsyncMock(return_value=None),
    )
    assert await format_deploy_line() == ""


@pytest.mark.asyncio
async def test_format_deploy_line_local_only(monkeypatch):
    monkeypatch.setattr(
        "bot.services.deploy_info.read_deploy_sha",
        lambda: "abcdef1234567890",
    )
    monkeypatch.setattr(
        "bot.services.deploy_info.fetch_remote_sha",
        AsyncMock(return_value=None),
    )
    line = await format_deploy_line()
    assert "Deploy:" in line
    assert "abcdef1" in line
    assert "—" in line


@pytest.mark.asyncio
async def test_format_deploy_line_both_shas(monkeypatch):
    monkeypatch.setattr(
        "bot.services.deploy_info.read_deploy_sha",
        lambda: "1111111111111111",
    )
    monkeypatch.setattr(
        "bot.services.deploy_info.fetch_remote_sha",
        AsyncMock(return_value="2222222222222222"),
    )
    line = await format_deploy_line()
    assert "1111111" in line
    assert "2222222" in line


def test_format_startup_admin_message(monkeypatch):
    monkeypatch.setattr(
        "bot.services.deploy_info.read_deploy_sha",
        lambda: "abcdef1234567890",
    )
    text = format_startup_admin_message("3.44.4")
    assert "3.44.4" in text
    assert "abcdef1" in text


def test_format_startup_admin_message_with_privacy_warn(monkeypatch):
    monkeypatch.setattr("bot.services.deploy_info.read_deploy_sha", lambda: None)
    text = format_startup_admin_message("1.0.0", privacy_warn="⚠️ Privacy")
    assert "1.0.0" in text
    assert "Privacy" in text
