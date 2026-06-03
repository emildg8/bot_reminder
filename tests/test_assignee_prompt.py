from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.keyboards.inline import assignee_choice_keyboard
from bot.services.assignee_prompt import offer_assignee_choice, should_offer_assignee_choice
from bot.services.pending_assignee import (
    clear_pending_assignee,
    get_pending_assignee,
    pop_pending_assignee,
)


def test_should_offer_assignee_choice_requires_multiple_without_time():
    assert should_offer_assignee_choice(["alice", "bobby"], "созвон без времени")
    assert not should_offer_assignee_choice(["alice"], "созвон")
    assert not should_offer_assignee_choice(
        ["alice", "bobby"],
        "через час созвон",
    )


def test_should_offer_assignee_choice_unresolved_plain_with_at_in_phrase():
    assert should_offer_assignee_choice(
        ["alice"],
        "созвон",
        mention_unresolved=True,
    )
    assert not should_offer_assignee_choice(
        ["alice"],
        "созвон",
        mention_unresolved=False,
    )


def test_format_assignee_choice_prompt_unresolved_plain():
    from bot.texts.messages import format_assignee_choice_prompt

    text = format_assignee_choice_prompt(
        ["alice"],
        unresolved_plain_name="Emil",
    )
    assert "Emil" in text
    assert "@alice" in text


def test_assignee_keyboard_has_none_option():
    kb = assignee_choice_keyboard(["alice", "bobby"])
    data = [btn.callback_data for row in kb.inline_keyboard for btn in row]
    assert "as:0" in data
    assert "as:1" in data
    assert "as:_none" in data
    assert "as:_cancel" in data


@pytest.mark.asyncio
async def test_offer_assignee_choice_stores_pending():
    from bot.services.nlp.schemas import ParsedReminder

    user_id = 88001
    clear_pending_assignee(user_id)
    message = SimpleNamespace()
    message.chat = SimpleNamespace(id=-100, type="supergroup", title="G")
    message.answer = AsyncMock()
    parsed = [ParsedReminder(text="тест", kind="once", delay_seconds=3600)]

    offered = await offer_assignee_choice(
        message,
        user_id=user_id,
        parsed_items=parsed,
        phrase="созвон",
        candidates=["alice", "bobby"],
        timezone="Europe/Moscow",
        delivery_chat_id=-100,
        source_label="",
        heard_text="",
    )
    assert offered is True
    message.answer.assert_awaited()
    pending = get_pending_assignee(user_id)
    assert pending is not None
    assert pending.candidates == ("alice", "bobby")
    pop_pending_assignee(user_id)
