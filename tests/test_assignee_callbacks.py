"""Callback as:* — выбор assignee и отмена."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from aiogram.enums import ChatType

from bot.handlers.menu import assignee_selected
from bot.services.chat_ctx import ChatKind
from bot.services.nlp.schemas import ParsedReminder
from bot.services.pending_assignee import (
    PendingAssigneeCreate,
    clear_pending_assignee,
    get_pending_assignee,
    pop_pending_assignee,
    store_pending_assignee,
)
from tests.callback_helpers import make_bot, make_callback


def _pending(user_id: int) -> PendingAssigneeCreate:
    return PendingAssigneeCreate(
        user_id=user_id,
        parsed_items=[
            ParsedReminder(text="созвон", kind="once", delay_seconds=3600, run_at=None)
        ],
        phrase="созвон",
        candidates=("alice", "bobby"),
        timezone="Europe/Moscow",
        delivery_chat_id=-100123,
        source_label="",
        heard_text="",
        collective_chat_id=-100123,
        collective_chat_kind=ChatKind.SUPERGROUP,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_assignee_cancel_clears_pending(monkeypatch):
    monkeypatch.setattr("bot.handlers.menu.safe_callback_answer", AsyncMock())
    user_id = 99201
    clear_pending_assignee(user_id)
    store_pending_assignee(_pending(user_id))
    deliver = AsyncMock()
    monkeypatch.setattr("bot.handlers.menu.deliver_create_confirm", deliver)

    callback = make_callback("as:_cancel", user_id, chat_id=-100123)
    callback.message.chat.type = ChatType.SUPERGROUP

    await assignee_selected(callback, make_bot())

    assert get_pending_assignee(user_id) is None
    deliver.assert_not_awaited()
    callback.message.edit_reply_markup.assert_awaited()


@pytest.mark.asyncio
async def test_assignee_pick_user_delivers_confirm(monkeypatch):
    monkeypatch.setattr("bot.handlers.menu.safe_callback_answer", AsyncMock())
    deliver = AsyncMock()
    resolve = AsyncMock(return_value=4242)
    monkeypatch.setattr("bot.handlers.menu.deliver_create_confirm", deliver)
    monkeypatch.setattr("bot.handlers.menu.resolve_mention_user_id", resolve)

    user_id = 99202
    clear_pending_assignee(user_id)
    store_pending_assignee(_pending(user_id))

    callback = make_callback("as:1", user_id, chat_id=-100123)
    callback.message.chat.type = ChatType.SUPERGROUP

    await assignee_selected(callback, make_bot())

    deliver.assert_awaited_once()
    kw = deliver.await_args.kwargs
    assert kw["mention_username"] == "bobby"
    assert kw["mention_provided"] is True
    assert pop_pending_assignee(user_id) is None
    resolve.assert_awaited()


@pytest.mark.asyncio
async def test_assignee_only_me_delivers_without_username(monkeypatch):
    monkeypatch.setattr("bot.handlers.menu.safe_callback_answer", AsyncMock())
    deliver = AsyncMock()
    monkeypatch.setattr("bot.handlers.menu.deliver_create_confirm", deliver)
    monkeypatch.setattr("bot.handlers.menu.resolve_mention_user_id", AsyncMock(return_value=None))

    user_id = 99203
    store_pending_assignee(_pending(user_id))
    callback = make_callback("as:_none", user_id, chat_id=-100123)

    await assignee_selected(callback, make_bot())

    kw = deliver.await_args.kwargs
    assert kw["mention_username"] is None
    assert kw["mention_provided"] is False


@pytest.mark.asyncio
async def test_assignee_expired_shows_alert(monkeypatch):
    answer = AsyncMock()
    monkeypatch.setattr("bot.handlers.menu.safe_callback_answer", answer)
    deliver = AsyncMock()
    monkeypatch.setattr("bot.handlers.menu.deliver_create_confirm", deliver)

    user_id = 99204
    clear_pending_assignee(user_id)
    callback = make_callback("as:0", user_id)

    await assignee_selected(callback, make_bot())

    deliver.assert_not_awaited()
    answer.assert_awaited()
    assert answer.await_args.kwargs.get("show_alert") is True
