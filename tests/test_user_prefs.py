from bot.services.user_prefs import (
    clamp_snooze_minutes,
    format_snooze_minutes,
    parse_snooze_presets,
)


def test_parse_snooze_presets():
    assert parse_snooze_presets("5,15,30,60") == [5, 15, 30, 60]
    assert parse_snooze_presets("5, 180, 240") == [5, 180, 240]


def test_format_snooze_minutes():
    assert format_snooze_minutes(15) == "15 мин"
    assert format_snooze_minutes(60) == "1 час"
    assert format_snooze_minutes(180) == "3 часа"


def test_clamp_snooze():
    assert clamp_snooze_minutes(1) == 5
    assert clamp_snooze_minutes(9999) == 1440
