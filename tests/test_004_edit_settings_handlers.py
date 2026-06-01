from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.db.repository import create_reminder, get_or_create_user
from bot.handlers.edit import cmd_edit, edit_button
from bot.handlers.settings import cycle_step, menu_settings, set_presets_std
from bot.services.drafts import clear_edit_pending, pop_edit_pending
from bot.services.user_prefs import get_snooze_presets, get_snooze_step
from tests.callback_helpers import make_bot, make_callback, make_message


async def _seed_reminder(session, user_id: int, text: str = "редактировать"):
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
async def test_edit_button_starts_edit_session(patched_db):
    user_id = 9300
    reminder = await _seed_reminder(patched_db, user_id)
    clear_edit_pending(user_id)
    callback = make_callback(f"edit:{reminder.id}", user_id)

    await edit_button(callback, make_bot())

    assert pop_edit_pending(user_id) == reminder.id
    body = callback.message.answer.await_args[0][0]
    assert f"#{reminder.id}" in body


@pytest.mark.asyncio
async def test_edit_button_denied_for_other_user(patched_db):
    owner_id = 9301
    reminder = await _seed_reminder(patched_db, owner_id)
    callback = make_callback(f"edit:{reminder.id}", 99999)

    await edit_button(callback, make_bot())

    assert "свои" in callback.message.answer.await_args[0][0].lower()
    assert pop_edit_pending(99999) is None


@pytest.mark.asyncio
async def test_cmd_edit_id_only_starts_session(patched_db):
    owner_id = 9310
    reminder = await _seed_reminder(patched_db, owner_id, "тест группы")
    message = make_message(owner_id)
    message.text = f"/edit {reminder.id}"

    await cmd_edit(message, make_bot())

    body = message.answer.await_args[0][0]
    assert f"#{reminder.id}" in body
    assert pop_edit_pending(owner_id) == reminder.id


@pytest.mark.asyncio
async def test_cmd_edit_hash_id(patched_db):
    owner_id = 9311
    reminder = await _seed_reminder(patched_db, owner_id)
    message = make_message(owner_id)
    message.text = f"/edit #{reminder.id}"

    await cmd_edit(message, make_bot())

    assert pop_edit_pending(owner_id) == reminder.id


@pytest.mark.asyncio
async def test_cmd_edit_without_args_shows_format(patched_db):
    user_id = 9302
    message = make_message(user_id)
    message.text = "/edit"

    await cmd_edit(message, make_bot())

    body = message.answer.await_args[0][0]
    assert "/edit 24" in body


@pytest.mark.asyncio
async def test_menu_settings_shows_snooze_options(patched_db):
    user_id = 9303
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    callback = make_callback("menu:settings", user_id)

    await menu_settings(callback)

    body = callback.message.answer.await_args[0][0]
    assert "Отложить" in body
    assert callback.message.answer.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_set_presets_std_updates_user(patched_db):
    user_id = 9304
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    callback = make_callback("set:pre:std", user_id)

    await set_presets_std(callback)

    presets = get_snooze_presets(user)
    assert presets == [5, 15, 30, 60]
    callback.answer.assert_awaited_with("Варианты обновлены")


@pytest.mark.asyncio
async def test_cycle_step_rotates_options(patched_db):
    user_id = 9305
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    callback = make_callback("set:step", user_id)

    await cycle_step(callback)

    step = get_snooze_step(await get_or_create_user(patched_db, user_id, "Europe/Moscow"))
    assert step in (5, 15, 30, 60)
    callback.message.edit_text.assert_awaited()
