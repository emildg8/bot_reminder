"""Help-тексты: re-export и обязательные подсказки по режимам чата."""

from bot.services.chat_ctx import ChatKind
from bot.texts import help as help_mod
from bot.texts.messages import (
    CREATE_HINT,
    EXAMPLES_INTRO,
    HELP_TEXT,
    HELP_TEXT_GROUP,
    HELP_TEXT_PRIVATE,
    format_help,
)


def test_help_reexports_match_messages():
    assert help_mod.HELP_TEXT is HELP_TEXT
    assert help_mod.CREATE_HINT is CREATE_HINT
    assert help_mod.EXAMPLES_INTRO is EXAMPLES_INTRO
    assert help_mod.EXAMPLES_TEXT is EXAMPLES_INTRO


def test_private_help_uses_placeholder_ids():
    assert "/edit N" in HELP_TEXT_PRIVATE
    assert "/delete N" in HELP_TEXT_PRIVATE
    assert "/edit 3" not in HELP_TEXT_PRIVATE
    assert "/delete 3" not in HELP_TEXT_PRIVATE


def test_group_help_assignee_and_delete_yes():
    text = format_help(ChatKind.SUPERGROUP)
    assert "На участника" in text
    assert "👤" in text
    assert "/delete" in text and "yes" in text.lower()
    assert "/remind" in text
    assert "/edit" in text


def test_group_help_via_format_matches_constant():
    assert format_help(ChatKind.SUPERGROUP) == HELP_TEXT_GROUP
    assert format_help(ChatKind.PRIVATE) == HELP_TEXT_PRIVATE
