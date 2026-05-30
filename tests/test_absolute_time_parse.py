from bot.services.nlp.absolute_time_parse import (
    normalize_time_dots,
    parse_absolute_datetime,
    try_dateparser_search,
)


def test_zavtra_v_14_dot():
    parsed = parse_absolute_datetime("бот анекдот завтра в 14.00", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert "анекдот" in parsed.text.lower()
    assert parsed.run_at.hour == 14
    assert parsed.run_at.minute == 0


def test_zavtra_task_after():
    parsed = parse_absolute_datetime("завтра в 14.00 создать бота анекдота", "Europe/Moscow")
    assert parsed is not None
    assert "анекдот" in parsed.text.lower()
    assert parsed.run_at.hour == 14


def test_segodnya():
    parsed = parse_absolute_datetime("сегодня в 18:30 ужин", "Europe/Moscow")
    assert parsed is not None
    assert "ужин" in parsed.text.lower()


def test_poslezavtra():
    parsed = parse_absolute_datetime("послезавтра в 10:00 созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 10


def test_normalize_dots():
    assert "14:00" in normalize_time_dots("завтра в 14.00")


def test_v_time_then_day():
    parsed = parse_absolute_datetime("в 14:00 завтра созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert "созвон" in parsed.text.lower()


def test_at_time_only():
    parsed = parse_absolute_datetime("в 14:00 созвон", "Europe/Moscow")
    assert parsed is not None
    assert "созвон" in parsed.text.lower()


def test_integration_rule_parser():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("бот анекдот завтра в 14.00", "Europe/Moscow")
    assert parsed is not None
    assert "анекдот" in parsed.text.lower()
    assert parsed.run_at.hour == 14


def test_dateparser_search_optional():
    result = try_dateparser_search("встреча 15 мая в 15:00", "Europe/Moscow")
    if result is not None:
        assert result.kind == "once"
        assert "встреча" in result.text.lower()
