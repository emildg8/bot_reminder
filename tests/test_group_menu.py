from aiogram.enums import ChatType
from aiogram.types import Chat

from bot.services.group_menu import is_group_menu_chat
from bot.texts.messages import format_group_commands_hint, format_group_private_only


def _chat(chat_type: ChatType) -> Chat:
    return Chat(id=-100123, type=chat_type)


def test_is_group_menu_chat():
    assert is_group_menu_chat(_chat(ChatType.GROUP))
    assert is_group_menu_chat(_chat(ChatType.SUPERGROUP))
    assert not is_group_menu_chat(_chat(ChatType.CHANNEL))
    assert not is_group_menu_chat(_chat(ChatType.PRIVATE))


def test_group_commands_hint():
    text = format_group_commands_hint("mybot")
    assert "/remind@mybot" in text
    assert "/list" in text
    assert "Меню" not in text


def test_private_only_message():
    assert "личке" in format_group_private_only()
