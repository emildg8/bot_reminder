from bot.services.nlp.weekday_parse import find_custom_weekly, parse_weekday_tokens


def test_parse_weekday_tokens():
    assert parse_weekday_tokens("пн ср пт") == [0, 2, 4]


def test_each_monday():
    result = find_custom_weekly("каждый понедельник в 9:00 отчёт")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [0]
    assert hour == 9
    assert minute == 0
    assert "отчёт" in task.lower()


def test_pn_sr_pt():
    result = find_custom_weekly("пн ср пт в 10:00 тренировка")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [0, 2, 4]
    assert hour == 10
    assert "тренировка" in task.lower()


def test_single_friday():
    result = find_custom_weekly("пт в 10:00 тренировка")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [4]
    assert hour == 10


def test_in_friday():
    result = find_custom_weekly("в пятницу в 10:00 созвон")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [4]
    assert "созвон" in task.lower()


def test_each_monday_no_time():
    result = find_custom_weekly("каждый понедельник отчёт")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [0]
    assert hour == 9
    assert "отчёт" in task.lower()


def test_each_tuesday_bare_hour():
    result = find_custom_weekly("каждый вторник в 10:00 отчет")
    assert result is not None
    weekdays, hour, minute, task = result
    assert weekdays == [1]
    assert hour == 10
    assert minute == 0
    assert task.lower() == "отчет"


def test_each_tuesday_full_name_not_truncated():
    from bot.services.nlp.rule_parser import parse_with_rules

    parsed = parse_with_rules("каждый вторник в 10 отчет", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "weekly"
    assert parsed.daily_time.hour == 10
    assert parsed.text.lower() == "отчет"


def test_multi_weekday_multi_time():
    from bot.services.nlp.rule_parser import parse_all_with_rules

    text = "Во вторник, среду, пятницу и субботу в 10.55, 16.10 и в 21.00 Экспа"
    results = parse_all_with_rules(text, "Europe/Moscow")
    assert len(results) == 3
    for parsed in results:
        assert parsed.kind == "weekly"
        assert parsed.weekdays == [1, 2, 4, 5]
        assert parsed.text == "Экспа"
    times = sorted(p.daily_time.strftime("%H:%M") for p in results)
    assert times == ["10:55", "16:10", "21:00"]

