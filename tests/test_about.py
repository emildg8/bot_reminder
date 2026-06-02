from bot.keyboards.inline import (
    about_screen_keyboard,
    author_screen_keyboard,
    developer_links_keyboard,
)
from bot.services.chat_ctx import ChatKind
from bot.texts.messages import (
    DEVELOPER_GITHUB_REPO,
    DEVELOPER_TAGLINE,
    DEVELOPER_TELEGRAM,
    developer_urls,
    format_about,
    format_developer_card,
    format_developer_teaser,
    format_help,
    format_help_feedback_footer,
)
from bot.version import __version__


def test_format_about_contains_version_and_teaser():
    text = format_about(__version__)
    assert __version__ in text
    assert "Дневник" in text
    assert "/author" in text
    assert DEVELOPER_TELEGRAM in text
    assert "Pet-project" not in text


def test_format_developer_teaser_release_link():
    text = format_developer_teaser(version="9.9.9")
    assert "9.9.9" in text
    assert developer_urls()["releases"] in text


def test_format_developer_card_links():
    text = format_developer_card(version=__version__)
    urls = developer_urls()
    assert DEVELOPER_TAGLINE in text
    assert f"@{DEVELOPER_TELEGRAM}" in text
    assert DEVELOPER_GITHUB_REPO in text
    assert urls["issues"] in text
    assert urls["profile"] in text
    assert __version__ in text


def test_format_help_feedback_footer():
    footer = format_help_feedback_footer()
    assert DEVELOPER_TELEGRAM in footer
    assert "Issues" in footer


def test_format_help_includes_author_footer():
    text = format_help(ChatKind.PRIVATE)
    assert format_help_feedback_footer().strip() in text


def test_developer_links_keyboard_urls():
    kb = developer_links_keyboard(include_thanks=False)
    urls = {btn.url for row in kb.inline_keyboard for btn in row if btn.url}
    expected = {
        developer_urls()["telegram"],
        developer_urls()["github"],
        developer_urls()["issues"],
        developer_urls()["releases"],
    }
    assert expected <= urls


def test_about_and_author_keyboards_have_nav():
    about_data = [
        btn.callback_data
        for row in about_screen_keyboard().inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    author_data = [
        btn.callback_data
        for row in author_screen_keyboard().inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    assert "menu:author" in about_data
    assert "menu:home" in about_data
    assert "menu:about" in author_data


def test_developer_keyboard_thanks_callback_when_enabled(monkeypatch):
    monkeypatch.setattr("bot.services.stars_tips.tips_enabled", lambda: True)
    kb = developer_links_keyboard(include_thanks=True)
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "menu:thanks" in callbacks
