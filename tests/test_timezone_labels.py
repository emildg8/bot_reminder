from bot.services.timezone_labels import format_timezone_label


def test_moscow():
    assert "Москва" in format_timezone_label("Europe/Moscow")


def test_gmt_offset():
    assert "UTC+3" in format_timezone_label("Etc/GMT-3")
