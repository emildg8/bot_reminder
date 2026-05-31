from unittest.mock import AsyncMock

import pytest

from bot.services.ambiguous_prompt import offer_ambiguous_time_choice
from bot.services.drafts import pop_edit_pending
from bot.services.pending_tasks import get_pending_task, pop_pending_task


@pytest.mark.asyncio
async def test_offer_ambiguous_hour_shows_keyboard():
    message = AsyncMock()
    message.answer = AsyncMock()

    handled = await offer_ambiguous_time_choice(message, "завтра в 2 созвон", 42)

    assert handled is True
    message.answer.assert_awaited_once()
    pending = get_pending_task(42)
    assert pending is not None
    assert pending.ambiguous_hour == 2
    assert pending.text == "созвон"
    pop_pending_task(42)


@pytest.mark.asyncio
async def test_offer_ambiguous_day_only():
    message = AsyncMock()
    message.answer = AsyncMock()

    handled = await offer_ambiguous_time_choice(message, "завтра созвон", 43)

    assert handled is True
    pending = get_pending_task(43)
    assert pending is not None
    assert pending.ambiguous_hour is None
    pop_pending_task(43)


@pytest.mark.asyncio
async def test_offer_ambiguous_skips_normal_phrase():
    message = AsyncMock()
    message.answer = AsyncMock()

    handled = await offer_ambiguous_time_choice(message, "через час созвон", 44)

    assert handled is False
    message.answer.assert_not_awaited()


@pytest.mark.asyncio
async def test_offer_ambiguous_keeps_edit_pending():
    message = AsyncMock()
    message.answer = AsyncMock()

    await offer_ambiguous_time_choice(
        message, "завтра в 2 созвон", 45, edit_reminder_id=9
    )

    assert pop_edit_pending(45) == 9
    pop_pending_task(45)
