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
