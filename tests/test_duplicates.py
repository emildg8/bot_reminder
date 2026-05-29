from bot.services.duplicates import normalize_text


def test_normalize_text():
    assert normalize_text("  Hello   World  ") == "hello world"


def test_normalize_cyrillic():
    assert normalize_text("Выпить  таблетки") == "выпить таблетки"
