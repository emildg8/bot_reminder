from bot.services.nlp.ambiguous_time import (
    detect_ambiguous_day_hour,
    phrase_from_ambiguous_choice,
)


def test_detect_zavtra_v_2():
    amb = detect_ambiguous_day_hour("завтра в 2 создать бота")
    assert amb is not None
    assert amb.hour == 2
    assert amb.task == "создать бота"
    assert amb.day == "завтра"


def test_not_ambiguous_with_dnya():
    assert detect_ambiguous_day_hour("завтра в 2 дня созвон") is None


def test_not_ambiguous_with_colon_time():
    assert detect_ambiguous_day_hour("завтра в 2:00 созвон") is None


def test_phrase_day_choice():
    phrase = phrase_from_ambiguous_choice(
        task="созвон",
        day="завтра",
        hour=2,
        choice="day",
    )
    assert "14:00" in phrase
    assert "созвон" in phrase


def test_phrase_night_choice():
    phrase = phrase_from_ambiguous_choice(
        task="созвон",
        day="завтра",
        hour=2,
        choice="night",
    )
    assert "02:00" in phrase
