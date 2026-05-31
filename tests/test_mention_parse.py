from bot.services.mention_parse import extract_leading_username


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
