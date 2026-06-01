from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.db.repository import create_reminder, get_or_create_user
from bot.handlers.list_callbacks import list_noop, list_page, list_tab
from bot.handlers.menu import menu_home, menu_list
from tests.callback_helpers import make_callback
from tests.db_helpers import patched_db


async def _seed_reminder(session, user_id: int, text: str = "напоминание"):
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
async def test_menu_list_empty(patched_db):
    callback = make_callback("menu:list", 9100)

    await menu_list(callback)

    callback.message.answer.assert_awaited()
    body = callback.message.answer.await_args[0][0]
    assert "Нет активных" in body


@pytest.mark.asyncio
async def test_menu_list_shows_reminders(patched_db):
    user_id = 9101
    await _seed_reminder(patched_db, user_id, "купить молоко")
    callback = make_callback("menu:list", user_id)

    await menu_list(callback)

    body = callback.message.answer.await_args[0][0]
    assert "купить молоко" in body
    assert "Активные" in body


@pytest.mark.asyncio
async def test_menu_home_shows_inline_menu(patched_db):
    callback = make_callback("menu:home", 9102)

    await menu_home(callback)

    callback.message.edit_text.assert_awaited_once()
    assert "Меню" in callback.message.edit_text.await_args[0][0]
    markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "menu:create" in callbacks
    assert "menu:list" in callbacks


@pytest.mark.asyncio
async def test_list_page_edits_active_list(patched_db):
    user_id = 9103
    await _seed_reminder(patched_db, user_id, "звонок")
    callback = make_callback("list:page:0", user_id)

    await list_page(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert "звонок" in body
    assert "Активные" in body


@pytest.mark.asyncio
async def test_list_page_pagination(patched_db):
    user_id = 9104
    for i in range(9):
        await _seed_reminder(patched_db, user_id, f"task-{i}")
    callback = make_callback("list:page:1", user_id)

    await list_page(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert "task-8" in body
    assert "2/2" in body


@pytest.mark.asyncio
async def test_list_tab_history_empty(patched_db):
    callback = make_callback("list:tab:history:0", 9105)

    await list_tab(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert "История" in body
    assert "Пока пусто" in body


@pytest.mark.asyncio
async def test_list_noop_answers(patched_db):
    callback = make_callback("list:noop", 9106)

    await list_noop(callback)

    callback.answer.assert_awaited()
