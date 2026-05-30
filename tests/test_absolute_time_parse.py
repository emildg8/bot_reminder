from bot.services.nlp.absolute_time_parse import (
    normalize_phrase,
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


def test_normalize_bare_hour():
    assert "2:00" in normalize_phrase("завтра в 2 создать бота")


def test_napomnyu_zavtra_v_2_chasa_dnya():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("Напомню завтра в 2 часа дня создать встречу", "Europe/Moscow")
    assert parsed is not None
    assert parsed.text.lower() == "создать встречу"
    assert parsed.run_at.hour == 14
    assert parsed.run_at.minute == 0


def test_zavtra_v_2_dnya_shorthand():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("завтра в 2 дня созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert "созвон" in parsed.text.lower()


def test_vecherom():
    parsed = parse_absolute_datetime("завтра в 8 вечера ужин", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 20
    assert "ужин" in parsed.text.lower()


def test_nochyu():
    parsed = parse_absolute_datetime("завтра в 2 часа ночи позвонить", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 2
    assert "позвонить" in parsed.text.lower()


def test_napomnyu_zavtra_v_2():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("Напомню завтра в 2 создать бота", "Europe/Moscow")
    assert parsed is not None
    assert parsed.text.lower() == "создать бота"
    assert parsed.run_at.hour == 2
    assert parsed.run_at.minute == 0


def test_napomnyu_with_comma():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("Напомню, завтра в 2:00 создать бота", "Europe/Moscow")
    assert parsed is not None
    assert "бот" in parsed.text.lower()
    assert parsed.run_at.hour == 2


def test_normalize_dots():
    assert "14:00" in normalize_phrase("завтра в 14.00")


def test_dateparser_search_zavtra_v_2():
    result = try_dateparser_search("Напомню завтра в 2 создать бота", "Europe/Moscow")
    assert result is not None
    assert result.run_at.hour == 2
    assert result.run_at.minute == 0
    assert "бот" in result.text.lower()


def test_v_time_then_day():
    parsed = parse_absolute_datetime("в 14:00 завтра созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert "созвон" in parsed.text.lower()


def test_zavtra_bez_vremeni():
    parsed = parse_absolute_datetime("завтра созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert "созвон" in parsed.text.lower()
    assert parsed.run_at.hour == 9


def test_sozvon_zavtra():
    parsed = parse_absolute_datetime("созвон завтра", "Europe/Moscow")
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
