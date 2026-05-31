from bot.services.chat_ctx import is_group_chat
from bot.services.telegram_format import format_reminder_message


def test_is_group_chat():
    assert is_group_chat(-100123)
    assert not is_group_chat(12345)


def test_private_no_mention():
    text = format_reminder_message("выпить воду", chat_id=12345)
    assert "выпить воду" in text
    assert "tg://user" not in text


def test_group_mentions_creator():
    text = format_reminder_message(
        "стендап",
        creator_user_id=99,
        creator_username="boss",
        chat_id=-1001,
    )
    assert "tg://user?id=99" in text
    assert "@boss" in text


def test_explicit_mention():
    text = format_reminder_message(
        "задача",
        mention_user_id=42,
        mention_username="alice",
        chat_id=-1001,
    )
    assert "tg://user?id=42" in text
    assert "@alice" in text


def test_channel_signature():
    text = format_reminder_message(
        "новый пост",
        chat_id=-100200,
        chat_type="channel",
        chat_title="Мой канал",
    )
    assert "Мой канал" in text
    assert "новый пост" in text
    assert "tg://user" not in text
