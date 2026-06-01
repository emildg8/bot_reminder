"""Ключевые фразы из docs/guides/nlp-time-priority.md."""

import pytest

from bot.services.nlp.ambiguous_time import (
    detect_ambiguous_day_hour,
    detect_ambiguous_day_only,
)
from bot.services.nlp.absolute_time_parse import normalize_phrase
from bot.services.nlp.rule_parser import parse_with_rules

TZ = "Europe/Moscow"


@pytest.mark.parametrize(
    ("phrase", "delay_seconds", "task"),
    [
        ("через 1 минуту тест", 60, "тест"),
        ("сегодня через 1 минуту тест", 60, "тест"),
        ("завтра через 2 дня оплатить", 2 * 86400, "оплатить"),
        ("завтра через час созвон", 3600, "созвон"),
        ("созвон сегодня через 10 минут", 600, "созвон"),
    ],
)
def test_relative_priority(phrase, delay_seconds, task):
    parsed = parse_with_rules(phrase, TZ)
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.delay_seconds == delay_seconds
    assert parsed.text == task


@pytest.mark.parametrize(
    ("phrase", "hour", "task_substr"),
    [
        ("завтра в 14.00 создать бота", 14, "бот"),
        ("завтра в 2 дня созвон", 14, "созвон"),
        ("завтра в 2 часа дня созвон", 14, "созвон"),
    ],
)
def test_absolute_time(phrase, hour, task_substr):
    parsed = parse_with_rules(phrase, TZ)
    assert parsed is not None
    assert parsed.kind == "once"
    assert parsed.run_at.hour == hour
    assert task_substr in parsed.text.lower()


@pytest.mark.parametrize(
    ("phrase", "kind", "interval_seconds"),
    [
        ("каждые 2 часа встать", "interval", 7200),
        ("завтра каждые 2 часа встать", "interval", 7200),
        ("каждые полчаса встать", "interval", 1800),
    ],
)
def test_schedule_interval(phrase, kind, interval_seconds):
    parsed = parse_with_rules(phrase, TZ)
    assert parsed is not None
    assert parsed.kind == kind
    assert parsed.interval_seconds == interval_seconds
    assert "завтра" not in parsed.text.lower()
    assert "встать" in parsed.text.lower()


@pytest.mark.parametrize(
    "phrase",
    [
        "сегодня через 1 минуту тест",
        "завтра через 2 дня оплатить",
        "завтра каждые 2 часа встать",
        "завтра в 2 дня созвон",
        "завтра в 14:00 созвон",
    ],
)
def test_no_ambiguous_day_only(phrase):
    assert detect_ambiguous_day_only(phrase) is None


@pytest.mark.parametrize(
    "phrase",
    [
        "сегодня через 1 минуту тест",
        "завтра в 2 дня созвон",
        "завтра в 14:00 созвон",
    ],
)
def test_no_ambiguous_day_hour(phrase):
    assert detect_ambiguous_day_hour(phrase) is None


def test_ambiguous_day_only_still_works():
    assert detect_ambiguous_day_only("завтра созвон") is not None


def test_ambiguous_day_hour_still_works():
    amb = detect_ambiguous_day_hour("завтра в 2 созвон")
    assert amb is not None
    assert amb.hour == 2


def test_normalize_does_not_break_cherez_dva_dnya():
    assert "14:00" not in normalize_phrase("завтра через 2 дня оплатить")
    assert "14:00" in normalize_phrase("завтра в 2 дня созвон")
