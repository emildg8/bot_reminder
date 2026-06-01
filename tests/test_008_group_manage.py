import pytest
from unittest.mock import AsyncMock

from bot.db.repository import create_reminder, get_or_create_user
from bot.handlers.manage import cmd_delete, cmd_pause
from bot.services.chat_ctx import ChatKind
from bot.texts.messages import format_help
from tests.callback_helpers import make_bot, make_message


@pytest.mark.asyncio
async def test_group_help_mentions_delete_and_edit():
    text = format_help(ChatKind.SUPERGROUP)
    assert "/delete" in text
    assert "/edit" in text


@pytest.mark.asyncio
async def test_del_alias_shows_confirm(patched_db):
    user_id = 9510
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    reminder = await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=-100700,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text="тест del",
        kind="once",
        next_run_at=None,
    )
    message = make_message(user_id, chat_id=-100700)
    message.text = f"/del {reminder.id}"

    await cmd_delete(message, make_bot())

    assert f"#{reminder.id}" in message.answer.await_args[0][0]


@pytest.mark.asyncio
async def test_delete_denied_for_other_user(patched_db):
    owner_id = 9511
    user = await get_or_create_user(patched_db, owner_id, "Europe/Moscow")
    reminder = await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=-100701,
        created_by_telegram_id=owner_id,
        timezone="Europe/Moscow",
        text="чужое",
        kind="once",
        next_run_at=None,
    )
    message = make_message(99988, chat_id=-100701)
    message.text = f"/delete {reminder.id}"

    await cmd_delete(message, make_bot())

    assert "свои" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_pause_requires_admin_in_group(patched_db, monkeypatch):
    monkeypatch.setattr(
        "bot.handlers.manage.can_manage_group_reminders",
        AsyncMock(return_value=False),
    )
    message = make_message(9512, chat_id=-100702)
    message.text = "/pause"

    await cmd_pause(message, make_bot())

    assert "администратор" in message.answer.await_args[0][0].lower()
