from bot.services.nlp.rule_parser import parse_with_rules
from bot.services.nlp.speech_cleanup import cleanup_stt_text, is_stt_text_too_short


def test_cherez_dva_chasa():
    parsed = parse_with_rules("через два часа созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.text == "созвон"
    assert parsed.run_at is not None


def test_cherez_tri_minuty():
    parsed = parse_with_rules("через три минуты таблетки", "Europe/Moscow")
    assert parsed is not None
    assert "таблет" in parsed.text.lower()


def test_kazhdye_dva_chasa():
    parsed = parse_with_rules("каждые два часа встать", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "interval"
    assert parsed.interval_seconds == 7200


def test_stt_typo_zapomni():
    text = cleanup_stt_text("запомни завтра в два часа дня созвон")
    assert "напомни" in text or "14:00" in text


def test_stt_too_short():
    assert is_stt_text_too_short("созвон")
    assert not is_stt_text_too_short("через час созвон")


def test_cherez_tri_chetyre_chasa():
    parsed = parse_with_rules("через три-четыре часа созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.text == "созвон"
    assert parsed.run_at is not None
