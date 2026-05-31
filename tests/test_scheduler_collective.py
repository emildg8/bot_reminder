from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.services.scheduler import _send_to_collective_chat


@pytest.mark.asyncio
async def test_collective_send_html_ok():
    bot = AsyncMock()
    ok = await _send_to_collective_chat(
        bot,
        chat_id=-100,
        reminder_id=1,
        text="<b>test</b>",
        collective_hint="\n\nhint",
        plain_text="test",
    )
    assert ok is True
    bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_collective_send_fallback_plain():
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=[Exception("html fail"), None])
    ok = await _send_to_collective_chat(
        bot,
        chat_id=-100,
        reminder_id=2,
        text="<b>bad</b>",
        collective_hint="",
        plain_text="тест",
    )
    assert ok is True
    assert bot.send_message.await_count == 2
    second_call = bot.send_message.await_args_list[1]
    assert second_call.kwargs.get("parse_mode") is None
    assert "тест" in second_call.kwargs["text"]


@pytest.mark.asyncio
async def test_collective_send_both_fail():
    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=Exception("forbidden"))
    ok = await _send_to_collective_chat(
        bot,
        chat_id=-100,
        reminder_id=3,
        text="x",
        collective_hint="",
        plain_text="x",
    )
    assert ok is False
