from datetime import datetime
from zoneinfo import ZoneInfo

from unittest.mock import AsyncMock

import pytest

from bot.db.repository import create_reminder, get_reminder, get_or_create_user
from bot.handlers.callbacks import (
    delete_confirm,
    delete_reminder,
    done_reminder,
    snooze_apply,
    snooze_menu,
)
from bot.services.snooze_picker import clear_picker, set_picker
from tests.callback_helpers import make_callback, patch_scheduler
from tests.db_helpers import patched_db


async def _seed_reminder(session, user_id: int, text: str = "отложить"):
    user = await get_or_create_user(session, user_id, "Europe/Moscow")
    return await create_reminder(
        session,
        user_id=user.id,
        chat_id=user_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text=text,
        kind="once",
        next_run_at=datetime(2030, 4, 1, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )


@pytest.mark.asyncio
async def test_delete_reminder_deactivates(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9010
    reminder = await _seed_reminder(patched_db, user_id, "удалить меня")
    callback = make_callback(f"delete:{reminder.id}", user_id)
    bot = AsyncMock()

    await delete_reminder(callback, bot)

    updated = await get_reminder(patched_db, reminder.id)
    assert updated is not None
    assert updated.is_active is False
    callback.message.edit_text.assert_awaited_with("🗑 Напоминание удалено.")


@pytest.mark.asyncio
async def test_delete_confirm_shows_prompt(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9011
    reminder = await _seed_reminder(patched_db, user_id)
    callback = make_callback(f"del_confirm:{reminder.id}", user_id)

    await delete_confirm(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert f"#{reminder.id}" in body
    assert callback.message.edit_text.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_delete_denied_for_other_user(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    owner_id = 9012
    other_id = 99999
    reminder = await _seed_reminder(patched_db, owner_id)
    callback = make_callback(f"delete:{reminder.id}", other_id)
    bot = AsyncMock()

    await delete_reminder(callback, bot)

    callback.answer.assert_awaited()
    assert "доступ" in callback.answer.await_args[0][0].lower()
    updated = await get_reminder(patched_db, reminder.id)
    assert updated.is_active is True


@pytest.mark.asyncio
async def test_snooze_apply_reschedules(patched_db, monkeypatch):
    scheduled = patch_scheduler(monkeypatch)
    user_id = 9013
    reminder = await _seed_reminder(patched_db, user_id)
    set_picker(user_id, reminder.id, 15)
    callback = make_callback(f"sza:{reminder.id}", user_id)
    bot = AsyncMock()

    await snooze_apply(callback, bot)

    updated = await get_reminder(patched_db, reminder.id)
    assert updated.next_run_at is not None
    assert len(scheduled) == 1
    body = callback.message.edit_text.await_args[0][0]
    assert "Отложено" in body
    clear_picker(user_id)


@pytest.mark.asyncio
async def test_snooze_menu_opens_picker(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9014
    reminder = await _seed_reminder(patched_db, user_id, "таблетки")
    callback = make_callback(f"szm:{reminder.id}", user_id)

    await snooze_menu(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert "таблетки" in body
    assert "Отложить" in body
    assert callback.message.edit_text.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_done_denied_for_other_user(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    owner_id = 9015
    reminder = await _seed_reminder(patched_db, owner_id)
    callback = make_callback(f"done:{reminder.id}", 88888)
    bot = AsyncMock()

    await done_reminder(callback, bot)

    assert "доступ" in callback.answer.await_args[0][0].lower()
    updated = await get_reminder(patched_db, reminder.id)
    assert updated.is_active is True
