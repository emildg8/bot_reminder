from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType

from bot.db.repository import get_or_create_user
from bot.handlers.create import cmd_remind
from bot.handlers.group_menu import gmenu_legacy
from tests.callback_helpers import make_bot, make_callback, patch_create_flow, patch_scheduler


def _group_message(user_id: int, text: str) -> MagicMock:
    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.username = "tester"
    message.chat.id = -100123456
    message.chat.type = ChatType.SUPERGROUP
    message.chat.title = "Test Group"
    message.text = text
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_gmenu_list_sends_active_list(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    user_id = 9500
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    callback = make_callback("gmenu:list", user_id, chat_id=-100123456)
    callback.message.chat.type = ChatType.SUPERGROUP

    await gmenu_legacy(callback)

    callback.message.answer.assert_awaited()


@pytest.mark.asyncio
async def test_gmenu_legacy_dismisses_other(patched_db):
    callback = make_callback("gmenu:home", 9501, chat_id=-100123456)
    callback.message.chat.type = ChatType.SUPERGROUP
    callback.message.edit_reply_markup = AsyncMock()

    await gmenu_legacy(callback)

    callback.answer.assert_awaited()


@pytest.mark.asyncio
async def test_cmd_remind_group_stores_draft(patched_db, monkeypatch):
    patch_scheduler(monkeypatch)
    patch_create_flow(monkeypatch)
    collective_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("bot.handlers.create.send_collective_confirm", collective_mock)
    user_id = 9502
    message = _group_message(user_id, "/remind@bot через 30 минут созвон")
    command = MagicMock()
    command.args = "через 30 минут созвон"

    await cmd_remind(message, command, make_bot())

    collective_mock.assert_awaited()
