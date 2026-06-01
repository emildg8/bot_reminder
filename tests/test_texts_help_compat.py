"""Re-export bot.texts.help — покрытие и обратная совместимость."""

from bot.texts import help as help_mod
from bot.texts.messages import CREATE_HINT, EXAMPLES_INTRO, HELP_TEXT


def test_help_reexports_match_messages():
    assert help_mod.HELP_TEXT is HELP_TEXT
    assert help_mod.CREATE_HINT is CREATE_HINT
    assert help_mod.EXAMPLES_INTRO is EXAMPLES_INTRO
    assert help_mod.EXAMPLES_TEXT is EXAMPLES_INTRO
