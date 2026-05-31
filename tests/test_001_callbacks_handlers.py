from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from bot.db.repository import create_reminder, get_active_chat_reminders, get_or_create_user, get_reminder
from bot.handlers.callbacks import (
    _create_from_draft,
    cancel_draft,
    confirm_edit_reminder,
    confirm_reminder,
    done_reminder,
)
from bot.services.drafts import get_draft, store_draft
from bot.services.nlp.schemas import ParsedReminder
from tests.db_helpers import patched_db


def _once_parsed(text: str = "тест", *, hour: int = 12) -> ParsedReminder:
    tz = ZoneInfo("Europe/Moscow")
    return ParsedReminder(
        text=text,
        kind="once",
        run_at=datetime(2030, 1, 15, hour, 0, tzinfo=tz),
    )


def _make_callback(data: str, user_id: int, chat_id: int = 90001) -> MagicMock:
    callback = MagicMock()
    callback.data = data
    callback.from_user.id = user_id
    callback.from_user.username = "tester"
    callback.message.chat.id = chat_id
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    return callback


def _patch_scheduler(monkeypatch) -> list:
    scheduled: list[tuple[int, datetime]] = []

    def fake_schedule(bot, reminder_id, next_run, *, timezone=None):
        scheduled.append((reminder_id, next_run))

    monkeypatch.setattr("bot.services.reminder_create.schedule_reminder", fake_schedule)
    monkeypatch.setattr("bot.handlers.callbacks.schedule_reminder", fake_schedule)
    monkeypatch.setattr(
        "bot.services.reminder_create.setup_channel_telegram_schedule",
        AsyncMock(),
    )
    monkeypatch.setattr("bot.handlers.callbacks.setup_channel_telegram_schedule", AsyncMock())
    monkeypatch.setattr("bot.services.reminder_create.log_reminder_event", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.log_reminder_event", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.cancel_reminder_job", lambda *_: None)
    monkeypatch.setattr("bot.handlers.callbacks.teardown_reminder_schedule", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.menu_keyboard_for_chat", lambda _chat_id: None)
    monkeypatch.setattr("bot.handlers.callbacks.safe_callback_answer", AsyncMock())
    return scheduled


@pytest.mark.asyncio
async def test_create_from_draft_missing(patched_db, monkeypatch):
    _patch_scheduler(monkeypatch)
    callback = _make_callback("confirm:missing", 100)
    bot = AsyncMock()

    await _create_from_draft(callback, bot, "missing")

    callback.answer.assert_awaited()
    assert callback.message.edit_text.await_count == 0


@pytest.mark.asyncio
async def test_confirm_reminder_creates_in_db(patched_db, monkeypatch):
    scheduled = _patch_scheduler(monkeypatch)
    user_id = 9001
    chat_id = user_id
    draft_id = store_draft(user_id, _once_parsed("купить хлеб"))
    callback = _make_callback(f"confirm:{draft_id}", user_id, chat_id=chat_id)
    bot = AsyncMock()

    await confirm_reminder(callback, bot)

    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    active = await get_active_chat_reminders(patched_db, chat_id)
    assert len(active) == 1
    assert active[0].text == "купить хлеб"
    assert active[0].user_id == user.id
    assert len(scheduled) == 1
    callback.message.edit_text.assert_awaited()
    assert get_draft(draft_id, user_id) is None


@pytest.mark.asyncio
async def test_confirm_shows_duplicate_warning(patched_db, monkeypatch):
    _patch_scheduler(monkeypatch)
    user_id = 9002
    chat_id = user_id
    run_at = datetime(2030, 1, 15, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=chat_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text="купить хлеб",
        kind="once",
        next_run_at=run_at,
    )
    draft_id = store_draft(user_id, _once_parsed("купить хлеб"))
    callback = _make_callback(f"confirm:{draft_id}", user_id, chat_id=chat_id)
    bot = AsyncMock()

    await _create_from_draft(callback, bot, draft_id)

    edit_args = callback.message.edit_text.await_args[0][0]
    assert "Похожее" in edit_args
    assert get_draft(draft_id, user_id) is None
    active = await get_active_chat_reminders(patched_db, chat_id)
    assert len(active) == 1
    assert callback.message.edit_text.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_confirm_force_creates_despite_duplicate(patched_db, monkeypatch):
    _patch_scheduler(monkeypatch)
    user_id = 9003
    chat_id = user_id
    run_at = datetime(2030, 1, 15, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=chat_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text="купить хлеб",
        kind="once",
        next_run_at=run_at,
    )
    draft_id = store_draft(user_id, _once_parsed("купить хлеб"))
    callback = _make_callback(f"confirm_force:{draft_id}", user_id, chat_id=chat_id)
    bot = AsyncMock()

    await _create_from_draft(callback, bot, draft_id, skip_duplicate=True)

    active = await get_active_chat_reminders(patched_db, chat_id)
    assert len(active) == 2


@pytest.mark.asyncio
async def test_cancel_draft(patched_db, monkeypatch):
    user_id = 9004
    draft_id = store_draft(user_id, _once_parsed())
    callback = _make_callback(f"cancel:{draft_id}", user_id)

    await cancel_draft(callback)

    assert get_draft(draft_id, user_id) is None
    callback.message.edit_text.assert_awaited_with("Отменено.")


@pytest.mark.asyncio
async def test_confirm_edit_updates_reminder(patched_db, monkeypatch):
    _patch_scheduler(monkeypatch)
    user_id = 9005
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    old_run = datetime(2030, 1, 15, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    reminder = await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=user_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text="старое",
        kind="once",
        next_run_at=old_run,
    )
    new_parsed = _once_parsed("новое", hour=14)
    draft_id = store_draft(user_id, new_parsed, edit_reminder_id=reminder.id)
    callback = _make_callback(f"confirm_edit:{reminder.id}:{draft_id}", user_id)
    bot = AsyncMock()

    await confirm_edit_reminder(callback, bot)

    updated = await get_reminder(patched_db, reminder.id)
    assert updated is not None
    assert updated.text == "новое"
    assert updated.is_active is True
    callback.message.edit_text.assert_awaited()


@pytest.mark.asyncio
async def test_done_reminder_deactivates(patched_db, monkeypatch):
    _patch_scheduler(monkeypatch)
    user_id = 9006
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    reminder = await create_reminder(
        patched_db,
        user_id=user.id,
        chat_id=user_id,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text="закрыть",
        kind="once",
        next_run_at=datetime(2030, 3, 1, 9, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    callback = _make_callback(f"done:{reminder.id}", user_id)
    bot = AsyncMock()

    await done_reminder(callback, bot)

    updated = await get_reminder(patched_db, reminder.id)
    assert updated is not None
    assert updated.is_active is False
    callback.message.edit_text.assert_awaited_with("✅ Готово. Напоминание закрыто.")
