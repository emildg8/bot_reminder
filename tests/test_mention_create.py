from types import SimpleNamespace

from bot.services.mention_create import (
    CreateMention,
    extract_create_mention,
    extract_reply_target,
    mention_was_provided,
)


def _msg(
    text: str,
    *,
    entities: list | None = None,
    reply_user: SimpleNamespace | None = None,
):
    message = SimpleNamespace()
    message.text = text
    message.caption = None
    message.entities = entities or []
    if reply_user:
        reply = SimpleNamespace()
        reply.from_user = reply_user
        message.reply_to_message = reply
    else:
        message.reply_to_message = None
    return message


def test_extract_reply_target_skips_bot():
    message = _msg("hi", reply_user=SimpleNamespace(id=1, username="bot", is_bot=True))
    assert extract_reply_target(message) == (None, None)


def test_extract_reply_target_user():
    message = _msg("hi", reply_user=SimpleNamespace(id=42, username="ivan", is_bot=False))
    assert extract_reply_target(message) == (42, "ivan")


def test_explicit_mention_overrides_reply():
    text = "/remind@testbot @alice завтра созвон"
    entities = [
        SimpleNamespace(
            type="text_mention",
            offset=16,
            length=6,
            user=SimpleNamespace(id=100, username="alice", is_bot=False),
        ),
    ]
    reply = SimpleNamespace(id=200, username="bob", is_bot=False)
    mention = extract_create_mention(
        _msg(text, entities=entities, reply_user=reply),
        "завтра созвон",
        bot_username="testbot",
        bot_id=1,
    )
    assert mention.user_id == 100
    assert mention.username == "alice"
    assert mention.source == "text"


def test_reply_fallback_without_at():
    message = _msg(
        "/remind@testbot завтра созвон",
        reply_user=SimpleNamespace(id=200, username="bob", is_bot=False),
    )
    mention = extract_create_mention(
        message,
        "завтра созвон",
        bot_username="testbot",
        bot_id=1,
    )
    assert mention.user_id == 200
    assert mention.username == "bob"
    assert mention.source == "reply"
    assert mention.phrase == "завтра созвон"


def test_voice_trailing_mention():
    mention = extract_create_mention(
        _msg("завтра созвон"),
        "через час тест @alice",
        bot_username="mybot",
        bot_id=1,
        from_transcription=True,
    )
    assert mention.username == "alice"
    assert mention.phrase == "через час тест"
    assert mention.source == "text"


def test_voice_reply_assigns_target():
    message = _msg(
        "завтра созвон",
        reply_user=SimpleNamespace(id=55, username="voice_target", is_bot=False),
    )
    mention = extract_create_mention(
        message,
        "завтра созвон",
        bot_username="bot",
        bot_id=1,
        from_transcription=True,
    )
    assert mention.user_id == 55
    assert mention.source == "reply"


def test_mention_was_provided():
    assert mention_was_provided(CreateMention(1, "a", "x", "reply"))
    assert not mention_was_provided(CreateMention(None, None, "x", None))


def test_create_mention_pick_note_for_multiple_users():
    mention = extract_create_mention(
        _msg("@bot @alice @bobby через час задача"),
        "через час задача",
        bot_username="bot",
        bot_id=1,
    )
    assert mention.username == "bobby"
    assert mention.pick_note is not None
    assert "alice" in mention.pick_note
