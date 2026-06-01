from datetime import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from bot.db.repository import create_reminder, get_or_create_user
from bot.handlers.list_callbacks import list_noop, list_page, list_tab, search_noop, search_page
from bot.handlers.menu import (
    example_picked,
    menu_about,
    menu_examples,
    menu_help,
    menu_home,
    menu_list,
    menu_more,
    menu_search,
    menu_status,
    menu_timezone,
)
from bot.texts.messages import EXAMPLES_INTRO
from bot.services.drafts import clear_search_pending, pop_search_pending
from bot.services.search_ui import _store_cache, send_search_results
from bot.version import __version__
from tests.callback_helpers import make_bot, make_callback, make_message


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


@pytest.mark.asyncio
async def test_menu_search_sets_pending_and_prompts(patched_db):
    user_id = 9107
    clear_search_pending(user_id)
    callback = make_callback("menu:search", user_id)

    await menu_search(callback)

    assert pop_search_pending(user_id) is True
    body = callback.message.answer.await_args[0][0]
    assert "Поиск" in body
    assert "/cancel" in body


@pytest.mark.asyncio
async def test_menu_more_shows_submenu(patched_db):
    callback = make_callback("menu:more", 9108)

    await menu_more(callback, AsyncMock())

    callback.message.edit_text.assert_awaited_once()
    assert "Дополнительно" in callback.message.edit_text.await_args[0][0]
    markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "menu:search" in callbacks
    assert "menu:examples" in callbacks


@pytest.mark.asyncio
async def test_search_page_shows_cached_results(patched_db):
    user_id = 9109
    first = await _seed_reminder(patched_db, user_id, "купить хлеб")
    second = await _seed_reminder(patched_db, user_id, "купить молоко")
    _store_cache(user_id, user_id, "купить", [first.id, second.id])
    callback = make_callback("search:page:0", user_id)

    await search_page(callback)

    body = callback.message.edit_text.await_args[0][0]
    assert "Найдено: 2" in body
    assert "купить" in body


@pytest.mark.asyncio
async def test_search_page_without_cache_alerts(patched_db):
    callback = make_callback("search:page:0", 9110)

    await search_page(callback)

    callback.answer.assert_awaited()
    alert = callback.answer.await_args.kwargs.get("text") or callback.answer.await_args[0][0]
    assert "устарел" in alert.lower()


@pytest.mark.asyncio
async def test_search_noop_answers(patched_db):
    callback = make_callback("search:noop", 9111)

    await search_noop(callback)

    callback.answer.assert_awaited()


@pytest.mark.asyncio
async def test_menu_help_shows_help_text(patched_db):
    callback = make_callback("menu:help", 9112)

    await menu_help(callback, AsyncMock())

    body = callback.message.answer.await_args[0][0]
    assert "голосом" in body


@pytest.mark.asyncio
async def test_menu_about_shows_version(patched_db):
    callback = make_callback("menu:about", 9113)

    await menu_about(callback)

    body = callback.message.answer.await_args[0][0]
    assert __version__ in body


@pytest.mark.asyncio
async def test_send_search_results_finds_matches(patched_db):
    user_id = 9114
    await _seed_reminder(patched_db, user_id, "купить хлеб")
    await _seed_reminder(patched_db, user_id, "позвонить маме")
    message = make_message(user_id)

    await send_search_results(message, "купить")

    body = message.answer.await_args[0][0]
    assert "Найдено: 1" in body
    assert "купить" in body
    assert message.answer.await_args.kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_send_search_results_empty(patched_db):
    user_id = 9115
    await _seed_reminder(patched_db, user_id, "только это")
    message = make_message(user_id)

    await send_search_results(message, "нет такого")

    body = message.answer.await_args[0][0]
    assert "ничего не найдено" in body.lower()


@pytest.mark.asyncio
async def test_menu_examples_shows_picker(patched_db):
    callback = make_callback("menu:examples", 9120)

    await menu_examples(callback, make_bot())

    callback.message.edit_text.assert_awaited_once()
    assert EXAMPLES_INTRO.split("<")[0].strip() in callback.message.edit_text.await_args[0][0]
    markup = callback.message.edit_text.await_args.kwargs["reply_markup"]
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert any(data.startswith("ex:") for data in callbacks)


@pytest.mark.asyncio
async def test_example_picked_shows_confirm(patched_db, monkeypatch):
    user_id = 9121
    monkeypatch.setattr(
        "bot.handlers.create.resolve_mention_user_id",
        AsyncMock(return_value=None),
    )
    callback = make_callback("ex:5", user_id)

    await example_picked(callback, make_bot())

    callback.message.answer.assert_awaited()
    body = callback.message.answer.await_args[0][0]
    assert "таблетки" in body
    markup = callback.message.answer.await_args.kwargs.get("reply_markup")
    assert markup is not None
    confirm_buttons = [
        btn.callback_data
        for row in markup.inline_keyboard
        for btn in row
        if btn.callback_data and btn.callback_data.startswith("confirm:")
    ]
    assert confirm_buttons


@pytest.mark.asyncio
async def test_example_invalid_shows_alert(patched_db):
    callback = make_callback("ex:999", 9122)

    await example_picked(callback, make_bot())

    callback.answer.assert_awaited()
    alert = callback.answer.await_args.kwargs.get("text") or callback.answer.await_args[0][0]
    assert "не найден" in alert.lower()


@pytest.mark.asyncio
async def test_menu_status_shows_active_count(patched_db):
    user_id = 9123
    await _seed_reminder(patched_db, user_id, "для статуса")
    callback = make_callback("menu:status", user_id)

    await menu_status(callback, make_bot())

    body = callback.message.answer.await_args[0][0]
    assert "Статус" in body
    assert "Активных: <b>1</b>" in body
    assert __version__ in body


@pytest.mark.asyncio
async def test_menu_timezone_shows_keyboard(patched_db):
    callback = make_callback("menu:timezone", 9124)

    await menu_timezone(callback, make_bot())

    body = callback.message.answer.await_args[0][0]
    assert "Часовой пояс" in body
    assert callback.message.answer.await_args.kwargs.get("reply_markup") is not None
