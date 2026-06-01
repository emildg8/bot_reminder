"""Unit-тесты admin_panel с in-memory БД (CI без data/)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.admin_panel import (
    BroadcastFilter,
    build_userinfo_reply,
    count_broadcast_recipients,
    fetch_recent_users,
    find_users_by_id_fragment,
    format_admin_panel_intro,
    format_admin_stats,
    format_quick_stats,
    format_recent_users,
    format_userfind_results,
    format_user_info,
    format_user_reminders,
    is_userinfo_card,
    notify_other_admins,
    parse_broadcast_message,
    parse_target_telegram_id,
    pop_pending_broadcast,
    set_pending_broadcast,
    userfind_keyboard,
)
from bot.db.repository import get_or_create_user


@pytest.mark.asyncio
async def test_format_quick_stats_empty_db(patched_db):
    text = await format_quick_stats()
    assert "польз." in text
    assert "7 дней" in text


@pytest.mark.asyncio
async def test_format_admin_panel_intro(patched_db):
    text = await format_admin_panel_intro()
    assert "Панель администратора" in text
    assert "/userfind" in text


@pytest.mark.asyncio
async def test_userinfo_and_reminders(patched_db):
    await get_or_create_user(patched_db, 900001, "Europe/Moscow")
    info = await format_user_info(900001)
    assert "900001" in info
    text, kb = await build_userinfo_reply(900001)
    assert "900001" in text
    assert kb is not None
    reminders = await format_user_reminders(900001)
    assert "нет активных" in reminders.lower()


@pytest.mark.asyncio
async def test_recent_users_and_find(patched_db):
    await get_or_create_user(patched_db, 900002, "Europe/Moscow")
    rows = await fetch_recent_users(limit=3)
    assert len(rows) >= 1
    recent = await format_recent_users()
    assert "900002" in recent
    found = await find_users_by_id_fragment("900002")
    assert 900002 in found
    text, kb = await format_userfind_results("900002")
    assert "900002" in text
    assert kb is not None
    assert userfind_keyboard(found) is not None


@pytest.mark.asyncio
async def test_broadcast_recipient_counts(patched_db):
    await get_or_create_user(patched_db, 900003, "Europe/Moscow")
    assert await count_broadcast_recipients(BroadcastFilter.ALL) >= 1
    assert await count_broadcast_recipients(BroadcastFilter.FREE) >= 1


@pytest.mark.asyncio
async def test_format_admin_stats(patched_db):
    await get_or_create_user(patched_db, 900004, "Europe/Moscow")
    stats = await format_admin_stats()
    assert "Статистика бота" in stats
    assert "планировщика" in stats


@pytest.mark.asyncio
async def test_pending_broadcast_roundtrip():
    set_pending_broadcast(99, "hello", filter=BroadcastFilter.ACTIVE)
    pending = pop_pending_broadcast(99)
    assert pending is not None
    assert pending.text == "hello"
    assert pending.filter == BroadcastFilter.ACTIVE


def test_parse_target_from_reply():
    msg = MagicMock()
    msg.text = "/userinfo"
    msg.reply_to_message = MagicMock()
    msg.reply_to_message.from_user = MagicMock(id=12345, is_bot=False)
    assert parse_target_telegram_id(msg) == 12345


def test_parse_broadcast_send_with_filter():
    msg = MagicMock()
    msg.text = "/broadcast да активные Go"
    parsed = parse_broadcast_message(msg)
    assert parsed is not None
    assert parsed.action == "send"
    assert parsed.filter == BroadcastFilter.ACTIVE
    assert parsed.text == "Go"


def test_is_userinfo_card():
    assert is_userinfo_card("👤 <b>Пользователь</b> 1")
    assert not is_userinfo_card("hello")


@pytest.mark.asyncio
async def test_notify_other_admins_skips_sender(monkeypatch):
    monkeypatch.setattr("bot.services.admin_panel.settings.admin_telegram_ids", [1, 2])
    bot = MagicMock()
    bot.send_message = AsyncMock()
    await notify_other_admins(bot, 1, "test")
    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args[0][0] == 2
