from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from bot.services.chat_ctx import ChatKind
from bot.services.collective_confirm import group_hint_failure_count, send_collective_confirm
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


def test_check_dm_with_preview():
    text = format_collective_check_dm(
        ChatKind.SUPERGROUP,
        "Test",
        preview="👤 @u · через 5 мин · задача",
    )
    assert "@u" in text
    assert "личке" in text


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
    dm_ok, hint_ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert dm_ok is True
    assert hint_ok is True
    assert bot.send_message.await_count == 2


@pytest.mark.asyncio
async def test_send_collective_confirm_with_reply():
    bot = AsyncMock()
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
        reply_to_message_id=999,
    )
    group_call = bot.send_message.await_args_list[1]
    assert group_call.kwargs.get("reply_to_message_id") == 999


@pytest.mark.asyncio
async def test_send_collective_confirm_hint_retry():
    bot = AsyncMock()
    bot.send_message.side_effect = [None, Exception("html"), None]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    dm_ok, hint_ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert dm_ok is True
    assert hint_ok is True
    assert bot.send_message.await_count == 3


@pytest.mark.asyncio
async def test_send_collective_confirm_hint_fail_increments_metric():
    bot = AsyncMock()
    bot.send_message.side_effect = [None, Exception("html"), Exception("plain")]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    before = group_hint_failure_count()
    dm_ok, hint_ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert dm_ok is True
    assert hint_ok is False
    assert group_hint_failure_count() == before + 1


@pytest.mark.asyncio
async def test_send_collective_confirm_dm_failed():
    bot = AsyncMock()
    bot.send_message.side_effect = [Exception("blocked")]
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    dm_ok, hint_ok = await send_collective_confirm(
        bot,
        user_id=123,
        collective_chat_id=-100,
        collective_kind=ChatKind.SUPERGROUP,
        chat_title="Team",
        body="Confirm body",
        reply_markup=kb,
    )
    assert dm_ok is False
    assert hint_ok is False
    assert bot.send_message.await_count == 1
