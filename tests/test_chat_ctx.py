from aiogram.enums import ChatType

from bot.services.chat_ctx import (
    ChatKind,
    chat_kind_from_id,
    chat_kind_from_type,
    collective_noun,
    collective_place_label,
    is_channel,
    is_collective_chat,
    is_group_like,
    is_private_chat,
    tz_scope_label,
)
from bot.texts.messages import (
    HELP_TEXT_CHANNEL,
    HELP_TEXT_GROUP,
    collective_created_suffix,
    format_channel_welcome,
    format_collective_confirm_prefix,
    format_help,
)


def test_chat_kind_from_id():
    assert chat_kind_from_id(123) == ChatKind.PRIVATE
    assert chat_kind_from_id(-100123, ChatType.CHANNEL) == ChatKind.CHANNEL
    assert chat_kind_from_id(-100123, ChatType.SUPERGROUP) == ChatKind.SUPERGROUP


def test_is_collective():
    assert is_collective_chat(-1001)
    assert not is_collective_chat(42)
    assert is_private_chat(42)


def test_is_channel():
    assert is_channel(ChatType.CHANNEL)
    assert not is_channel(ChatType.GROUP)


def test_labels():
    assert collective_place_label(ChatKind.CHANNEL) == "канале"
    assert collective_place_label(ChatKind.SUPERGROUP) == "группе"
    assert tz_scope_label(ChatKind.CHANNEL) == "канала"
    assert collective_noun(ChatKind.CHANNEL) == "канал"


def test_format_help_variants():
    assert "группе" in format_help(ChatKind.SUPERGROUP)
    assert "канале" in format_help(ChatKind.CHANNEL)
    assert "голосом" in format_help(ChatKind.PRIVATE)


def test_collective_suffix():
    assert "канале" in collective_created_suffix(ChatKind.CHANNEL)
    assert "группе" in collective_created_suffix(ChatKind.SUPERGROUP)


def test_confirm_prefix():
    assert "канале" in format_collective_confirm_prefix(ChatKind.CHANNEL)


def test_welcome_texts():
    assert "канале" in format_channel_welcome("mybot")
    assert "/remind@mybot" in format_channel_welcome("mybot")
