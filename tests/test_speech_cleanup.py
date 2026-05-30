from bot.services.nlp.speech_cleanup import cleanup_stt_text
from bot.services.nlp.rule_parser import parse_with_rules


def test_spaced_time():
    assert "14:00" in cleanup_stt_text("завтра 14 00 созвон")


def test_dash_time():
    assert "14:00" in cleanup_stt_text("завтра в 14-00 созвон")


def test_filler_words():
    text = cleanup_stt_text("э, напомни мне, завтра в 2 часа дня созвон")
    assert "э" not in text.lower().split()[0]
    assert "14:00" in text or "2" in text


def test_voice_phrase_end_to_end():
    parsed = parse_with_rules(
        cleanup_stt_text("Напомни завтра два часа дня посмотреть фильм"),
        "Europe/Moscow",
    )
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert "фильм" in parsed.text.lower()


def test_spoken_zero_zero():
    parsed = parse_with_rules(
        cleanup_stt_text("завтра четырнадцать ноль ноль созвон"),
        "Europe/Moscow",
    )
    assert parsed is not None
    assert parsed.run_at.hour == 14
