from bot.services.chat_ctx import ChatKind
from bot.texts.messages import format_parse_fail, looks_like_task_only, phrase_from_task_preset


def test_looks_like_task_only():
    assert looks_like_task_only("почистить зубы")
    assert looks_like_task_only("завтра созвон")  # без HH:MM — кнопки времени
    assert not looks_like_task_only("через час почистить зубы")
    assert not looks_like_task_only("завтра в 14:00 созвон")


def test_format_parse_fail_task_only():
    msg = format_parse_fail("почистить зубы")
    assert "почистить зубы" in msg
    assert "Выбери когда" in msg


def test_phrase_from_task_preset():
    assert "30 минут" in phrase_from_task_preset("почистить зубы", "30m")
    assert "завтра" in phrase_from_task_preset("почистить зубы", "tom14")


def test_format_parse_fail_group_hint():
    msg = format_parse_fail(
        "созвон завтра",
        chat_kind=ChatKind.SUPERGROUP,
        bot_username="mybot",
    )
    assert "/remind@mybot" in msg


def test_dm_failed_fallback_has_link():
    from bot.texts.messages import format_collective_dm_failed_fallback

    msg = format_collective_dm_failed_fallback("mybot")
    assert "t.me/mybot" in msg


def test_parse_fail_generic_constant():
    from bot.texts.messages import PARSE_FAIL

    assert "Не понял время" in PARSE_FAIL
