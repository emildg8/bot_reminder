from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.enums import ChatType

from bot.db.models import ReminderKind
from bot.services import channel_schedule as cs


def test_can_use_telegram_schedule_window():
    now = datetime.now(UTC)
    assert cs._can_use_telegram_schedule(now + timedelta(seconds=30)) is True
    assert cs._can_use_telegram_schedule(now + timedelta(seconds=5)) is False
    assert cs._can_use_telegram_schedule(now + timedelta(days=400)) is False


@pytest.mark.asyncio
async def test_try_schedule_channel_post_success():
    bot = AsyncMock()
    bot.return_value = MagicMock(message_id=42)
    run_at = datetime.now(UTC) + timedelta(hours=1)
    msg_id = await cs.try_schedule_channel_post(
        bot, channel_id=-100, text="test", run_at_utc=run_at
    )
    assert msg_id == 42
    bot.assert_awaited_once()


@pytest.mark.asyncio
async def test_try_schedule_channel_post_too_soon():
    bot = AsyncMock()
    run_at = datetime.now(UTC) + timedelta(seconds=3)
    msg_id = await cs.try_schedule_channel_post(
        bot, channel_id=-100, text="test", run_at_utc=run_at
    )
    assert msg_id is None
    bot.assert_not_awaited()


@pytest.mark.asyncio
async def test_setup_skips_non_channel():
    bot = AsyncMock()
    bot.get_chat = AsyncMock(return_value=MagicMock(type=ChatType.SUPERGROUP))
    session = AsyncMock()
    reminder = MagicMock(
        kind=ReminderKind.ONCE.value,
        chat_id=-100,
        next_run_at=datetime.now(UTC) + timedelta(hours=1),
        timezone="UTC",
        telegram_schedule_message_id=None,
        text="hi",
    )
    ok = await cs.setup_channel_telegram_schedule(bot, session, reminder)
    assert ok is False


@pytest.mark.asyncio
async def test_setup_schedules_once_reminder():
    bot = AsyncMock()
    bot.get_chat = AsyncMock(
        return_value=MagicMock(type=ChatType.CHANNEL, title="News")
    )
    session = AsyncMock()
    reminder = MagicMock(
        kind=ReminderKind.ONCE.value,
        chat_id=-100,
        next_run_at=datetime.now(UTC) + timedelta(hours=2),
        timezone="UTC",
        telegram_schedule_message_id=None,
        text="post",
        id=7,
    )
    with patch.object(cs, "try_schedule_channel_post", AsyncMock(return_value=99)):
        with patch(
            "bot.services.channel_schedule.update_reminder_telegram_schedule",
            AsyncMock(),
        ) as upd:
            ok = await cs.setup_channel_telegram_schedule(bot, session, reminder)
    assert ok is True
    upd.assert_awaited_once_with(session, reminder, 99)


@pytest.mark.asyncio
async def test_cancel_reminder_telegram_schedule():
    bot = AsyncMock()
    session = AsyncMock()
    reminder = MagicMock(chat_id=-100, telegram_schedule_message_id=55)
    with patch.object(cs, "cancel_channel_scheduled_post", AsyncMock()) as cancel:
        with patch(
            "bot.services.channel_schedule.update_reminder_telegram_schedule",
            AsyncMock(),
        ) as upd:
            await cs.cancel_reminder_telegram_schedule(bot, session, reminder)
    cancel.assert_awaited_once_with(bot, -100, 55)
    upd.assert_awaited_once_with(session, reminder, None)
