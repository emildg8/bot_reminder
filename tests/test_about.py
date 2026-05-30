from bot.texts.messages import format_about
from bot.version import __version__


def test_format_about_contains_version():
    text = format_about(__version__)
    assert __version__ in text
    assert "Дневник" in text
    assert "Статистика" in text
