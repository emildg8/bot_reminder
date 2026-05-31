from unittest.mock import MagicMock

import pytest

from bot.services.chat_delivery import resolve_delivery_chat_id


@pytest.mark.asyncio
async def test_delivery_same_chat(monkeypatch):
    async def fake_find(session, chat_id):
        return None

    monkeypatch.setattr(
        "bot.services.chat_delivery.find_channel_by_linked_chat",
        fake_find,
    )
    result = await resolve_delivery_chat_id(MagicMock(), -1001, "supergroup")
    assert result == -1001


@pytest.mark.asyncio
async def test_delivery_from_discussion(monkeypatch):
    async def fake_find(session, chat_id):
        return -2002 if chat_id == -1001 else None

    monkeypatch.setattr(
        "bot.services.chat_delivery.find_channel_by_linked_chat",
        fake_find,
    )
    result = await resolve_delivery_chat_id(MagicMock(), -1001, "supergroup")
    assert result == -2002
