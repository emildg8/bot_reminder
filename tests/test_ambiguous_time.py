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


def test_detect_day_only_zavtra_sozvon():
    from bot.services.nlp.ambiguous_time import detect_ambiguous_day_only, phrase_from_day_only_choice

    amb = detect_ambiguous_day_only("завтра созвон")
    assert amb is not None
    assert amb.day == "завтра"
    assert amb.task == "созвон"

    phrase = phrase_from_day_only_choice(task="созвон", day="завтра", choice="day")
    assert "14:00" in phrase
    assert "созвон" in phrase


def test_day_only_not_when_time_in_phrase():
    from bot.services.nlp.ambiguous_time import detect_ambiguous_day_only

    assert detect_ambiguous_day_only("завтра в 14:00 созвон") is None
    assert detect_ambiguous_day_only("завтра утром зарядка") is None


def test_day_only_not_when_relative_offset():
    from bot.services.nlp.ambiguous_time import detect_ambiguous_day_only

    assert detect_ambiguous_day_only("сегодня через 1 минуту тест") is None
    assert detect_ambiguous_day_only("завтра через час созвон") is None
    assert detect_ambiguous_day_only("сегодня через полчаса таблетки") is None


def test_day_only_not_when_schedule():
    from bot.services.nlp.ambiguous_time import detect_ambiguous_day_only

    assert detect_ambiguous_day_only("завтра каждые 2 часа встать") is None


def test_ambiguous_hour_keyboard_two_choices():
    from bot.keyboards.inline import ambiguous_hour_keyboard

    labels = [btn.text for row in ambiguous_hour_keyboard().inline_keyboard for btn in row]
    assert len(labels) == 2
    assert all("09:00" not in label for label in labels)


def test_detect_napomni_prefix():
    amb = detect_ambiguous_day_hour("напомни завтра в 2 созвон")
    assert amb is not None
    assert amb.task == "созвон"
    assert amb.hour == 2


def test_detect_zavtra_v_dva_slovom():
    amb = detect_ambiguous_day_hour("завтра в два созвон")
    assert amb is not None
    assert amb.hour == 2
    assert amb.task == "созвон"


def test_detect_suffix_sozvon_zavtra_v_2():
    amb = detect_ambiguous_day_hour("созвон завтра в 2")
    assert amb is not None
    assert amb.task == "созвон"
    assert amb.day == "завтра"
    assert amb.hour == 2


def test_detect_suffix_napomni():
    amb = detect_ambiguous_day_hour("напомни созвон завтра в два")
    assert amb is not None
    assert amb.task == "созвон"
    assert amb.hour == 2
