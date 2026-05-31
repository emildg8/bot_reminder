from aiogram.enums import ChatType
from aiogram.types import Chat

from bot.keyboards.inline import (
    group_examples_keyboard,
    group_home_keyboard,
    group_timezone_keyboard,
    group_timezone_offset_keyboard,
)
from bot.services.group_menu import group_screen_content, is_group_menu_chat
from bot.texts.messages import format_group_private_only


def _chat(chat_type: ChatType) -> Chat:
    return Chat(id=-100123, type=chat_type)


def test_is_group_menu_chat():
    assert is_group_menu_chat(_chat(ChatType.GROUP))
    assert is_group_menu_chat(_chat(ChatType.SUPERGROUP))
    assert not is_group_menu_chat(_chat(ChatType.CHANNEL))
    assert not is_group_menu_chat(_chat(ChatType.PRIVATE))


def test_group_screen_home():
    text, kb = group_screen_content("home", bot_username="mybot")
    assert "/remind@mybot" in text
    assert kb == group_home_keyboard()


def test_group_screen_examples():
    text, kb = group_screen_content("examples")
    assert "Примеры" in text
    assert kb == group_examples_keyboard()


def test_group_screen_tz():
    text, kb = group_screen_content("tz")
    assert "Часовой пояс" in text
    assert kb == group_timezone_keyboard()


def test_group_home_keyboard_callbacks():
    kb = group_home_keyboard()
    data = {btn.callback_data for row in kb.inline_keyboard for btn in row}
    assert data == {"gmenu:list", "gmenu:hint", "gmenu:tz", "gmenu:help", "gmenu:examples"}


def test_group_examples_back_to_home():
    kb = group_examples_keyboard()
    backs = [btn.callback_data for row in kb.inline_keyboard for btn in row if "Меню" in btn.text]
    assert backs == ["gmenu:home"]


def test_group_tz_offset_back():
    kb = group_timezone_offset_keyboard()
    backs = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.text == "◀️ Меню"]
    assert backs == ["gmenu:home"]


def test_private_only_message():
    assert "личке" in format_group_private_only()
