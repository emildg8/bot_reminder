from types import SimpleNamespace
from unittest.mock import MagicMock

from bot.handlers.create import _raw_for_assignee_candidates


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
