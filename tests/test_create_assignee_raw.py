from types import SimpleNamespace
from unittest.mock import MagicMock

from bot.handlers.create import (
    _message_text_or_caption,
    _raw_for_assignee_candidates,
)


def test_message_text_or_caption_ignores_magic_mock():
    message = MagicMock()
    message.text = MagicMock()
    message.caption = None
    assert _message_text_or_caption(message) is None


def test_raw_for_assignee_candidates_falls_back_to_phrase():
    message = SimpleNamespace(text=None, caption=None)
    raw = _raw_for_assignee_candidates(
        message,
        "завтра в 9:00 таблетки",
        source_label="",
    )
    assert raw == "завтра в 9:00 таблетки"


def test_raw_for_assignee_candidates_voice_uses_phrase():
    message = MagicMock()
    message.text = None
    message.caption = "@bot @alice созвон"
    raw = _raw_for_assignee_candidates(
        message,
        "@alice @bobby созвон",
        source_label="voice",
    )
    assert raw == "@alice @bobby созвон"
    assert "@bot" not in raw


def test_raw_for_assignee_candidates_text_uses_message():
    message = SimpleNamespace(
        text="@bot @alice @bobby созвон",
        caption=None,
    )
    raw = _raw_for_assignee_candidates(message, "созвон", source_label="")
    assert "@alice" in raw and "@bobby" in raw
