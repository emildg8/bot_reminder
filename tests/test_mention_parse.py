from types import SimpleNamespace

from bot.services.mention_parse import (
    extract_leading_username,
    extract_mention_from_message,
    extract_username_anywhere,
    extract_username_candidates,
    strip_text_before_bot_mention,
    strip_leading_bot_mention,
    _extract_leading_plain_name,
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


def test_extract_leading_username_for_user_prefix():
    username, clean = extract_leading_username("для @alice завтра в 10:00 созвон")
    assert username == "alice"
    assert "созвон" in clean


def test_extract_leading_username_napomni_prefix():
    username, clean = extract_leading_username("напомни @ivan через час задача")
    assert username == "ivan"
    assert clean == "через час задача"


def test_extract_leading_username_napominanie_dlya_prefix():
    username, clean = extract_leading_username("напоминание для @ivan через час задача")
    assert username == "ivan"
    assert clean == "через час задача"


def test_extract_username_trailing_after_time():
    username, clean = extract_username_anywhere("через час задача @alice")
    assert username == "alice"
    assert clean == "через час задача"


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


def test_strip_text_before_bot_mention_middle_of_phrase():
    clean = strip_text_before_bot_mention(
        "ребят смотрим @break_remind_bot + @mokew2222 через минуту тест",
        "break_remind_bot",
    )
    assert clean == "@mokew2222 через минуту тест"


def test_extract_mention_from_message_plus_separator():
    message = SimpleNamespace(
        text="@break_remind_bot + @mokew2222 через 1 минуту тест",
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
    assert clean == "через 1 минуту тест"


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


def test_extract_username_anywhere_drops_empty_brackets_after_mention():
    username, clean = extract_username_anywhere("через минуту тест (@alice)")
    assert username == "alice"
    assert clean == "через минуту тест"


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


def test_extract_username_anywhere_multiple_users_auto_nearest_time():
    username, clean = extract_username_anywhere(
        "@alice @bobby через час задача",
        bot_username="break_remind_bot",
    )
    assert username == "bobby"
    assert clean == "через час задача"
    assert "bobby" not in clean.lower()


def test_extract_username_anywhere_multiple_users_explicit_first():
    username, clean = extract_username_anywhere(
        "@alice @bobby через час задача",
        bot_username="break_remind_bot",
        pick="first",
    )
    assert username == "alice"
    assert clean == "через час задача"


def test_extract_username_anywhere_multiple_users_last_variant():
    username, clean = extract_username_anywhere(
        "@alice @bobby через час задача",
        bot_username="break_remind_bot",
        pick="last",
    )
    assert username == "bobby"
    assert clean == "через час задача"


def test_extract_username_anywhere_nearest_time_dot_clock():
    username, clean = extract_username_anywhere(
        "@alice @bobby в 18.20 созвон",
        bot_username="break_remind_bot",
        pick="nearest_time",
    )
    assert username == "bobby"
    assert clean == "в 18.20 созвон"


def test_extract_username_anywhere_nearest_time_prefers_user_before_time():
    username, clean = extract_username_anywhere(
        "@alice @bobby завтра в 10:00 созвон",
        bot_username="break_remind_bot",
        pick="nearest_time",
    )
    assert username == "bobby"
    assert clean == "завтра в 10:00 созвон"


def test_extract_username_anywhere_nearest_time_fallbacks_to_first():
    username, clean = extract_username_anywhere(
        "@alice @bobby просто созвон без времени",
        bot_username="break_remind_bot",
        pick="nearest_time",
    )
    assert username == "alice"
    assert clean == "просто созвон без времени"


def test_extract_username_candidates_list_and_clean():
    usernames, clean = extract_username_candidates(
        "@break_remind_bot @alice @bobby через час задача",
        bot_username="break_remind_bot",
    )
    assert usernames == ["alice", "bobby"]
    assert clean == "через час задача"


def test_extract_username_candidates_ignores_mentions_before_bot():
    usernames, clean = extract_username_candidates(
        "@alice ребят @break_remind_bot @bobby через час задача",
        bot_username="break_remind_bot",
    )
    assert usernames == ["bobby"]
    assert clean == "через час задача"


def test_extract_username_candidates_keeps_prefix_if_no_user_after_mid_bot():
    usernames, clean = extract_username_candidates(
        "через минуту @break_remind_bot тест",
        bot_username="break_remind_bot",
    )
    assert usernames == []
    assert clean == "через минуту @break_remind_bot тест"


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
    assert mention_username == "bobby"
    assert clean == "через час задача"


def test_assignee_pick_for_count():
    from bot.services.mention_parse import assignee_pick_for_count

    assert assignee_pick_for_count(1) == "first"
    assert assignee_pick_for_count(2) == "nearest_time"


def test_extract_leading_plain_name_before_time():
    name, clean = _extract_leading_plain_name("Emil Через 1 минуту тест")
    assert name == "Emil"
    assert clean == "Через 1 минуту тест"


def test_extract_leading_plain_name_skips_at_user():
    name, clean = _extract_leading_plain_name("@alice через час задача")
    assert name is None
    assert clean == "@alice через час задача"


def test_extract_mention_from_message_bot_and_display_name():
    """@бот + имя из списка Telegram (text_mention без @ в тексте)."""
    text = "@break_remind_bot Emil Через 1 минуту тест"
    entities = [
        SimpleNamespace(type="mention", offset=0, length=17),
        SimpleNamespace(
            type="text_mention",
            offset=18,
            length=4,
            user=SimpleNamespace(id=42, username="emildg8", is_bot=False),
        ),
    ]
    message = SimpleNamespace(
        text=text,
        caption=None,
        entities=entities,
        caption_entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id == 42
    assert mention_username == "emildg8"
    assert clean == "Через 1 минуту тест"


def test_extract_mention_from_message_plain_name_without_entity():
    """Имя набрано вручную — распознаём как assignee, но без user_id."""
    message = SimpleNamespace(
        text="@break_remind_bot Emil Через 1 минуту тест",
        caption=None,
        entities=[],
        caption_entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id is None
    assert mention_username == "Emil"
    assert clean == "Через 1 минуту тест"


def test_extract_mention_from_caption_entities():
    message = SimpleNamespace(
        text=None,
        caption="@break_remind_bot @alice через 1 минуту тест",
        entities=[],
        caption_entities=[
            SimpleNamespace(type="mention", offset=0, length=17),
            SimpleNamespace(type="mention", offset=18, length=6),
        ],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_username == "alice"
    assert clean == "через 1 минуту тест"


def test_utf16_emoji_before_bot_mention():
    """Emoji перед @бот — entity offset в UTF-16."""
    from bot.services.mention_parse import utf16_offset_to_index

    text = "👋@break_remind_bot Emil через 1 минуту"
    assert utf16_offset_to_index(text, 0) == 0
    assert utf16_offset_to_index(text, 2) == 1
    entities = [
        SimpleNamespace(type="mention", offset=2, length=17),
        SimpleNamespace(
            type="text_mention",
            offset=20,
            length=4,
            user=SimpleNamespace(id=7, username=None, is_bot=False),
        ),
    ]
    message = SimpleNamespace(
        text=text,
        caption=None,
        entities=entities,
        caption_entities=[],
    )
    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username="break_remind_bot",
        bot_id=1,
    )
    assert mention_id == 7
    assert mention_username == "Emil"
    assert "минуту" in clean
