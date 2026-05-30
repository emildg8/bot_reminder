from bot.services.nlp.rule_parser import parse_with_rules


def test_in_minutes_is_once_not_interval():
    parsed = parse_with_rules("через 30 минут выпить таблетки", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert "таблетки" in parsed.text.lower()


def test_interval_every_2_hours():
    parsed = parse_with_rules("каждые 2 часа встать", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "interval"
    assert parsed.interval_seconds == 7200


def test_weekdays():
    parsed = parse_with_rules("по будням в 09:00 зарядка", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "weekly"
    assert parsed.weekdays == [0, 1, 2, 3, 4]


def test_zavtra_v_14_dot():
    parsed = parse_with_rules("завтра в 14.00 создать бота анекдота", "Europe/Moscow")
    assert parsed is not None
    assert parsed.kind == "once"
    assert "анекдот" in parsed.text.lower()
    assert parsed.run_at.hour == 14
