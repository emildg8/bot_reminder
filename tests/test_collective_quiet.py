"""Tests for compact collective DM on fire."""

from bot.texts.messages import format_collective_dm_fired


def test_collective_dm_fired_compact():
    text = format_collective_dm_fired(21, "тест")
    assert "#21" in text
    assert "тест" in text
    assert "группе" not in text
