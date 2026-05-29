from bot.services.mention_parse import extract_leading_username


def test_extract_leading_username():
    username, clean = extract_leading_username("@alice через 1 час задача")
    assert username == "alice"
    assert clean == "через 1 час задача"


def test_no_username():
    username, clean = extract_leading_username("через 30 минут тест")
    assert username is None
    assert clean == "через 30 минут тест"
