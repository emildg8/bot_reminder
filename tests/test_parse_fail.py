from bot.texts.messages import format_parse_fail, looks_like_task_only


def test_looks_like_task_only():
    assert looks_like_task_only("почистить зубы")
    assert not looks_like_task_only("через час почистить зубы")
    assert not looks_like_task_only("завтра в 14:00 созвон")


def test_format_parse_fail_task_only():
    msg = format_parse_fail("почистить зубы")
    assert "почистить зубы" in msg
    assert "через 30 минут" in msg


def test_format_parse_fail_with_time_hint():
    msg = format_parse_fail("через когда-нибудь")
    assert "Не понял время" in msg
