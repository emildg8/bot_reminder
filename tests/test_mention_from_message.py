from types import SimpleNamespace

from bot.services.mention_parse import extract_mention_from_message


def _user(uid: int, username: str | None = "alice", *, is_bot: bool = False):
    return SimpleNamespace(id=uid, username=username, is_bot=is_bot)


def _msg(text: str, entities: list | None = None):
    return SimpleNamespace(text=text, caption=None, entities=entities or [])


def test_text_mention_in_remind_command():
    text = "/remind@testbot @alice завтра в 14:00 созвон"
    entities = [
        SimpleNamespace(
            type="text_mention",
            offset=16,
            length=6,
            user=_user(42, "alice"),
        ),
    ]
    mention_id, mention_username, clean = extract_mention_from_message(
        _msg(text, entities),
        bot_username="testbot",
        bot_id=1,
    )
    assert mention_id == 42
    assert mention_username == "alice"
    assert "созвон" in clean
    assert "alice" not in clean.lower()


def test_skips_bot_mention_then_takes_user():
    text = "@testbot @bob через час задача"
    entities = [
        SimpleNamespace(type="mention", offset=0, length=8),
        SimpleNamespace(type="mention", offset=9, length=4),
    ]
    mention_id, mention_username, clean = extract_mention_from_message(
        _msg(text, entities),
        bot_username="testbot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "bob"
    assert clean == "через час задача"


def test_multiple_user_entities_nearest_time_all_stripped():
    text = "@testbot @alice @bobby через час задача"
    entities = [
        SimpleNamespace(type="mention", offset=0, length=8),
        SimpleNamespace(type="mention", offset=9, length=6),
        SimpleNamespace(type="mention", offset=16, length=6),
    ]
    mention_id, mention_username, clean = extract_mention_from_message(
        _msg(text, entities),
        bot_username="testbot",
        bot_id=1,
    )
    assert mention_username == "bobby"
    assert clean == "через час задача"
    assert "bobby" not in clean.lower()


def test_text_mention_without_username():
    text = "@mybot @ivan завтра созвон"
    entities = [
        SimpleNamespace(type="mention", offset=0, length=6),
        SimpleNamespace(
            type="text_mention",
            offset=7,
            length=5,
            user=_user(99, None),
        ),
    ]
    mention_id, mention_username, clean = extract_mention_from_message(
        _msg(text, entities),
        bot_username="mybot",
        bot_id=1,
    )
    assert mention_id == 99
    assert mention_username is None
    assert "созвон" in clean
    assert "ivan" not in clean.lower()
