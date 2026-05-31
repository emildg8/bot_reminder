from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup

from bot.services.chat_ctx import ChatKind
from bot.services.collective_confirm import send_collective_confirm
from bot.texts.messages import (
    format_collective_check_dm,
    format_collective_created_notice,
    format_collective_dm_confirm_header,
)


def test_dm_confirm_header():
    assert "Моя группа" in format_collective_dm_confirm_header(
        ChatKind.SUPERGROUP, "Моя группа"
    )


def test_check_dm_text():
    text = format_collective_check_dm(ChatKind.SUPERGROUP, "Test")
    assert "личке" in text
    assert len(text) < 80


def test_created_notice():
    text = format_collective_created_notice(
        creator_username="alice",
        creator_user_id=1,
        reminder_id=5,
        when="через 1 мин",
        text="тест",
        chat_kind=ChatKind.SUPERGROUP,
    )
    assert "@alice" in text
    assert "#5" in text


@pytest.mark.asyncio
async def test_send_collective_confirm():
    bot = AsyncMock()
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert ok is True
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_send_collective_confirm_dm_failed():
    bot = AsyncMock()
    bot.send_message.side_effect = [Exception("blocked"), None]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert ok is False
    assert bot.send_message.await_count == 1
