from bot.services.nlp.absolute_time_parse import (
    normalize_phrase,
    parse_absolute_datetime,
    try_dateparser_search,
)


def test_at_time_only_dot_separator():
    parsed = parse_absolute_datetime("в 18.20 тест", "Europe/Moscow")
    assert parsed is not None
    assert parsed.text == "тест"
    assert parsed.run_at.hour == 18
    assert parsed.run_at.minute == 20


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


def test_normalize_compact_hhmm():
    assert "14:30" in normalize_phrase("сегодня в 1430")
    assert "9:30" in normalize_phrase("в 930")


def test_segodnya_v_1430_compact():
    parsed = parse_absolute_datetime(
        "написать егору в вацапе сегодня в 1430",
        "Europe/Moscow",
    )
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.run_at.hour == 14
    assert parsed.run_at.minute == 30
    assert "егор" in parsed.text.lower()
    assert "вацап" in parsed.text.lower()
    assert "1430" not in parsed.text
    assert "14:30" not in parsed.text


def test_segodnya_v_1430_rule_parser():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules(
        "Написать егору в вацапе сегодня в 1430",
        "Europe/Moscow",
    )
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert parsed.run_at.minute == 30


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


def test_zavtra_utrom():
    parsed = parse_absolute_datetime("завтра утром зарядка", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 9
    assert "зарядка" in parsed.text.lower()


def test_zavtra_dnem():
    parsed = parse_absolute_datetime("завтра днём созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14


def test_polovina_dnya():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("завтра в полтора дня обед", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 13
    assert parsed.run_at.minute == 30


def test_chetyrnadtsat_nol_nol():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("завтра четырнадцать ноль ноль созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14


def test_zavtra_k_obedy():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("завтра к обеду созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 13
    assert "созвон" in parsed.text.lower()


def test_poslezavtra_k_vecheru():
    parsed = parse_absolute_datetime("послезавтра к вечеру ужин", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 20
    assert "ужин" in parsed.text.lower()


def test_format_parse_fail_voice_heard():
    from bot.texts.messages import format_parse_fail

    msg = format_parse_fail("созвон", source="voice", heard="завтра созвон")
    assert "Распознано" in msg
    assert "созвон" in msg


def test_stt_dva_chasa_dnya_slovami():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("Напомни завтра два часа дня посмотреть фильм", "Europe/Moscow")
    assert parsed is not None
    assert parsed.text.lower() == "посмотреть фильм"
    assert parsed.run_at.hour == 14
    assert parsed.run_at.minute == 0


def test_stt_v_dva_slovom():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("завтра в два часа дня посмотреть фильм", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 14
    assert "фильм" in parsed.text.lower()


def test_napomnyu_zavtra_v_2_ambiguous():
    from bot.services.nlp.ambiguous_time import detect_ambiguous_day_hour

    amb = detect_ambiguous_day_hour("завтра в 2 создать бота")
    assert amb is not None
    assert amb.hour == 2
    assert "бот" in amb.task.lower()


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


def test_polovina_chetvertogo():
    parsed = parse_absolute_datetime("завтра в половине четвертого созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 3
    assert parsed.run_at.minute == 30
    assert parsed.text.lower() == "созвон"


def test_polovina_chetvertogo_dnya():
    parsed = parse_absolute_datetime("завтра в половине четвертого дня созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.hour == 15
    assert parsed.run_at.minute == 30
    assert "созвон" in parsed.text.lower()


def test_normalize_polovina_chetvertogo():
    assert "03:30" in normalize_phrase("завтра в половине четвертого")


def test_named_date_with_time():
    parsed = parse_absolute_datetime("15 июня в 10:00 созвон", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.day == 15
    assert parsed.run_at.month == 6
    assert parsed.run_at.hour == 10
    assert "созвон" in parsed.text.lower()


def test_named_date_default_morning():
    parsed = parse_absolute_datetime("20 декабря подарки", "Europe/Moscow")
    assert parsed is not None
    assert parsed.run_at.day == 20
    assert parsed.run_at.month == 12
    assert parsed.run_at.hour == 9
    assert "подарки" in parsed.text.lower()
