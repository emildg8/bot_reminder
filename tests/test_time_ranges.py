"""Тесты парсинга диапазонов времени."""

from bot.services.nlp.rule_parser import parse_with_rules


def test_parse_range_hours():
    parsed = parse_with_rules("через 3-4 часа созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.text == "созвон"
    assert parsed.run_at is not None


def test_parse_couple_hours():
    parsed = parse_with_rules("через пару часов обед", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert "обед" in parsed.text.lower() or parsed.text == "обед"


def test_parse_few_hours():
    parsed = parse_with_rules("через несколько часов созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
