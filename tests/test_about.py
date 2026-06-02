from bot.keyboards.inline import developer_links_keyboard
from bot.services.chat_ctx import ChatKind
from bot.texts.messages import (
    DEVELOPER_GITHUB_REPO,
    DEVELOPER_TELEGRAM,
    developer_urls,
    format_about,
    format_developer_card,
    format_help,
    format_help_feedback_footer,
)
from bot.version import __version__
from bot.keyboards.inline import about_developer_keyboard


def test_format_about_contains_version():
    text = format_about(__version__)
    assert __version__ in text
    assert "Дневник" in text
    assert "Разработчик" in text


def test_format_developer_card_links():
    text = format_developer_card()
    urls = developer_urls()
    assert "Pet-project" in text
    assert f"@{DEVELOPER_TELEGRAM}" in text
    assert DEVELOPER_GITHUB_REPO in text
    assert urls["issues"] in text
    assert urls["releases"] in text


def test_format_help_feedback_footer():
    footer = format_help_feedback_footer()
    assert DEVELOPER_TELEGRAM in footer
    assert "Issues" in footer


def test_format_help_includes_author_footer():
    text = format_help(ChatKind.PRIVATE)
    assert format_help_feedback_footer().strip() in text
    text_group = format_help(ChatKind.SUPERGROUP)
    assert DEVELOPER_TELEGRAM in text_group


def test_developer_links_keyboard_urls():
    kb = developer_links_keyboard(include_thanks=False)
    urls = {btn.url for row in kb.inline_keyboard for btn in row if btn.url}
    expected = set(developer_urls().values())
    assert expected <= urls


def test_developer_keyboard_thanks_callback_when_enabled(monkeypatch):
    monkeypatch.setattr("bot.services.stars_tips.tips_enabled", lambda: True)
    kb = developer_links_keyboard(include_thanks=True)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "menu:thanks" in callbacks


def test_about_developer_keyboard_alias():
    assert about_developer_keyboard().inline_keyboard == developer_links_keyboard().inline_keyboard
