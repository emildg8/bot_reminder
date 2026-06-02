from types import SimpleNamespace

from bot.services.mention_parse import (
    extract_leading_username,
    extract_mention_from_message,
    extract_username_anywhere,
    extract_username_candidates,
    strip_leading_bot_mention,
)


def test_extract_leading_username():
    username, clean = extract_leading_username("@alice через 1 час задача")
    assert username == "alice"
    assert clean == "через 1 час задача"


def test_no_username():
    username, clean = extract_leading_username("через 30 минут тест")
    assert username is None
    assert clean == "через 30 минут тест"


def test_skip_bot_username():
    username, clean = extract_leading_username(
        "@break_remind_bot через час созвон",
        bot_username="break_remind_bot",
    )
    assert username is None
    assert clean == "через час созвон"


def test_user_username_not_skipped():
    username, clean = extract_leading_username(
        "@alice через час созвон",
        bot_username="break_remind_bot",
    )
    assert username == "alice"
    assert clean == "через час созвон"


def test_strip_leading_bot_mention_plain():
    clean = strip_leading_bot_mention(
        "@break_remind_bot через минуту тест",
        "break_remind_bot",
    )
    assert clean == "через минуту тест"


def test_strip_leading_bot_mention_compact():
    clean = strip_leading_bot_mention(
        "@break_remind_bot@mokew2222 через минуту тест",
        "break_remind_bot",
    )
    assert clean == "@mokew2222 через минуту тест"


def test_extract_mention_from_message_compact_bot_then_user():
    message = SimpleNamespace(
        text="@break_remind_bot@mokew2222 через минуту тест",
        caption=None,
        entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "mokew2222"
    assert clean == "через минуту тест"


def test_extract_leading_username_with_plus_separator():
    username, clean = extract_leading_username("+ @alice через минуту тест")
    assert username == "alice"
    assert clean == "через минуту тест"


def test_extract_leading_username_with_dash_separator():
    username, clean = extract_leading_username("— @alice через минуту тест")
    assert username == "alice"
    assert clean == "через минуту тест"


def test_strip_leading_bot_mention_plus_separator():
    clean = strip_leading_bot_mention(
        "@break_remind_bot + @mokew2222 через минуту тест",
        "break_remind_bot",
    )
    assert clean == "@mokew2222 через минуту тест"


def test_strip_leading_bot_mention_dash_separator():
    clean = strip_leading_bot_mention(
        "@break_remind_bot — @mokew2222 через минуту тест",
        "break_remind_bot",
    )
    assert clean == "@mokew2222 через минуту тест"


def test_extract_mention_from_message_bot_dash_user():
    message = SimpleNamespace(
        text="@break_remind_bot — @mokew2222 через минуту тест",
        caption=None,
        entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "mokew2222"
    assert clean == "через минуту тест"


def test_extract_username_anywhere_trailing():
    username, clean = extract_username_anywhere("через минуту тест @alice")
    assert username == "alice"
    assert clean == "через минуту тест"


def test_extract_username_anywhere_trailing_punctuation():
    username, clean = extract_username_anywhere("через минуту тест @alice!")
    assert username == "alice"
    assert clean == "через минуту тест!"


def test_extract_username_anywhere_skips_bot_then_user():
    username, clean = extract_username_anywhere(
        "@break_remind_bot через минуту @alice",
        bot_username="break_remind_bot",
    )
    assert username == "alice"
    assert "alice" not in clean.lower()


def test_extract_mention_from_message_user_in_tail():
    message = SimpleNamespace(
        text="@break_remind_bot через минуту тест @mokew2222",
        caption=None,
        entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "mokew2222"
    assert clean == "через минуту тест"


def test_extract_username_anywhere_multiple_users_first_wins():
    username, clean = extract_username_anywhere(
        "@alice @bobby через час задача",
        bot_username="break_remind_bot",
    )
    assert username == "alice"
    assert clean == "через час задача"
    assert "bobby" not in clean.lower()


def test_extract_username_anywhere_multiple_users_last_variant():
    username, clean = extract_username_anywhere(
        "@alice @bobby через час задача",
        bot_username="break_remind_bot",
        pick="last",
    )
    assert username == "bobby"
    assert clean == "через час задача"


def test_extract_username_candidates_list_and_clean():
    usernames, clean = extract_username_candidates(
        "@break_remind_bot @alice @bobby через час задача",
        bot_username="break_remind_bot",
    )
    assert usernames == ["alice", "bobby"]
    assert clean == "через час задача"


def test_extract_leading_username_strips_second_user():
    username, clean = extract_leading_username("@alice @bobby через час задача")
    assert username == "alice"
    assert clean == "через час задача"


def test_extract_leading_username_comma_separator():
    username, clean = extract_leading_username("@alice,через час задача")
    assert username == "alice"
    assert clean == "через час задача"


def test_extract_mention_normalizes_whitespace():
    message = SimpleNamespace(
        text="@break_remind_bot   @mokew2222   через   минуту   тест",
        caption=None,
        entities=[],
    )
    _, _, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert clean == "через минуту тест"


def test_extract_mention_strips_inline_bot():
    message = SimpleNamespace(
        text="@break_remind_bot через минуту @break_remind_bot тест",
        caption=None,
        entities=[],
    )
    _, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_username is None
    assert clean == "через минуту тест"


def test_extract_mention_from_message_multiple_users_no_entities():
    message = SimpleNamespace(
        text="@break_remind_bot @alice @bobby через час задача",
        caption=None,
        entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "alice"
    assert clean == "через час задача"
