from types import SimpleNamespace
from unittest.mock import MagicMock

from aiogram.enums import ChatType

from bot.services.bot_mention import (
    is_bot_mentioned,
    should_handle_collective_message,
)


def _message(*, chat_id: int, chat_type: ChatType, text: str = "", entities=None):
    chat = SimpleNamespace(id=chat_id, type=chat_type)
    return SimpleNamespace(
        chat=chat,
        text=text,
        caption=None,
        entities=entities or [],
        from_user=SimpleNamespace(id=1),
    )


def test_private_always_handled():
    msg = _message(chat_id=123, chat_type=ChatType.PRIVATE, text="завтра созвон")
    assert should_handle_collective_message(msg, bot_username="bot", bot_id=1)


def test_group_requires_mention():
    msg = _message(chat_id=-100, chat_type=ChatType.SUPERGROUP, text="завтра созвон")
    assert not should_handle_collective_message(msg, bot_username="mybot", bot_id=1)

    msg2 = _message(chat_id=-100, chat_type=ChatType.SUPERGROUP, text="@mybot завтра созвон")
    assert should_handle_collective_message(msg2, bot_username="mybot", bot_id=1)

    msg3 = _message(
        chat_id=-100,
        chat_type=ChatType.SUPERGROUP,
        text="@mybot@alice через минуту тест",
    )
    assert should_handle_collective_message(msg3, bot_username="mybot", bot_id=1)


def test_channel_only_commands():
    msg = _message(chat_id=-100, chat_type=ChatType.CHANNEL, text="просто пост")
    assert not should_handle_collective_message(msg, bot_username="mybot", bot_id=1)

    cmd = _message(chat_id=-100, chat_type=ChatType.CHANNEL, text="/remind завтра пост")
    assert should_handle_collective_message(cmd, bot_username="mybot", bot_id=1)


def test_is_bot_mentioned_entity():
    msg = MagicMock()
    msg.text = "@mybot задача"
    msg.caption = None
    msg.entities = [SimpleNamespace(type="mention", offset=0, length=6)]
    assert is_bot_mentioned(msg, bot_username="mybot", bot_id=99)
