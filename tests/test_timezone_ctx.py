from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.services.timezone_ctx import collective_ops_chat_id


@pytest.mark.asyncio
async def test_collective_ops_same_chat(monkeypatch):
    session = MagicMock()

    async def fake_find(session, chat_id):
        return None

    monkeypatch.setattr(
        "bot.services.timezone_ctx.find_channel_by_linked_chat",
        fake_find,
    )
    assert await collective_ops_chat_id(session, -100) == -100


@pytest.mark.asyncio
async def test_collective_ops_linked_channel(monkeypatch):
    session = MagicMock()

    async def fake_find(session, chat_id):
        return -200

    monkeypatch.setattr(
        "bot.services.timezone_ctx.find_channel_by_linked_chat",
        fake_find,
    )
    assert await collective_ops_chat_id(session, -100) == -200
