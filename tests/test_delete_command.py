import pytest

from bot.db.repository import create_reminder, get_or_create_user, get_reminder
from bot.handlers.manage import cmd_delete
from tests.callback_helpers import make_bot, make_callback, make_message, patch_scheduler
async def _seed(session, user_id: int, text: str = "тест"):
    user = await get_or_create_user(session, user_id, "Europe/Moscow")
    return await create_reminder(
        session,
        user_id=user.id,
        chat_id=-100500,
        created_by_telegram_id=user_id,
        timezone="Europe/Moscow",
        text=text,
        kind="once",
        next_run_at=None,
    )


@pytest.mark.asyncio
async def test_delete_command_shows_confirm(patched_db):
    user_id = 9400
    reminder = await _seed(patched_db, user_id)
    message = make_message(user_id, chat_id=-100500)
    message.text = f"/delete {reminder.id}"

    await cmd_delete(message, make_bot())

    body = message.answer.await_args[0][0]
    assert f"#{reminder.id}" in body
    assert "Удалить" in body
    assert message.answer.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_delete_command_hash_id(patched_db):
    user_id = 9401
    reminder = await _seed(patched_db, user_id)
    message = make_message(user_id, chat_id=-100500)
    message.text = f"/delete #{reminder.id}"

    await cmd_delete(message, make_bot())

    assert f"#{reminder.id}" in message.answer.await_args[0][0]


@pytest.mark.asyncio
async def test_delete_command_yes_instant(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9403
    reminder = await _seed(patched_db, user_id, text="сразу")
    message = make_message(user_id, chat_id=-100500)
    message.text = f"/delete {reminder.id} yes"

    await cmd_delete(message, make_bot())

    refreshed = await get_reminder(patched_db, reminder.id)
    assert refreshed is not None
    assert refreshed.is_active is False
    body = message.answer.await_args[0][0]
    assert "удалено" in body.lower()
    assert message.answer.await_args.kwargs.get("reply_markup") is None


@pytest.mark.asyncio
async def test_delete_confirm_deactivates(patched_db, monkeypatch):
    from bot.handlers.callbacks import delete_reminder

    user_id = 9402
    reminder = await _seed(patched_db, user_id)
    callback = make_callback(f"delete:{reminder.id}", user_id, chat_id=-100500)
    patch_scheduler(monkeypatch)

    await delete_reminder(callback, make_bot())

    refreshed = await get_reminder(patched_db, reminder.id)
    assert refreshed is not None
    assert refreshed.is_active is False
    assert "удалено" in callback.message.edit_text.await_args[0][0].lower()
