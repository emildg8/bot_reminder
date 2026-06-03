from bot.keyboards.inline import (
    about_screen_keyboard,
    author_screen_keyboard,
    developer_links_keyboard,
    developer_made_by_keyboard,
)
from bot.services.chat_ctx import ChatKind
from bot.services.stars_tips import tip_thank_you_keyboard
from bot.texts.messages import (
    DEVELOPER_GITHUB_REPO,
    DEVELOPER_TAGLINE,
    DEVELOPER_TELEGRAM,
    developer_urls,
    format_about,
    format_developer_card,
    format_developer_made_by_line,
    format_developer_status_line,
    format_developer_support_note,
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
    assert developer_urls(version="9.9.9")["release_tag"] in text
    assert "что нового" in text


def test_format_developer_status_line():
    text = format_developer_status_line(version="8.8.8")
    assert DEVELOPER_TELEGRAM in text
    assert "/author" in text
    assert developer_urls(version="8.8.8")["release_tag"] in text


def test_format_status_includes_author_line():
    from bot.services.chat_ctx import ChatKind
    from bot.texts.messages import format_status

    line = format_developer_status_line()
    text = format_status(
        count=1,
        paused=False,
        tz="Europe/Moscow",
        tz_scope="личка",
        chat_kind=ChatKind.PRIVATE,
        author_line=line,
    )
    assert line in text


def test_tip_thank_you_keyboard_has_author():
    kb = tip_thank_you_keyboard()
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    assert "menu:author" in callbacks
    assert "menu:thanks" in callbacks


def test_format_developer_made_by_line():
    text = format_developer_made_by_line()
    assert DEVELOPER_TELEGRAM in text
    assert developer_urls()["github"] in text
    assert "код на GitHub" in text


def test_format_developer_support_note():
    text = format_developer_support_note()
    assert "не пиши" in text
    assert "личку" in text


def test_format_developer_card_includes_support_note():
    text = format_developer_card(version=__version__)
    assert format_developer_support_note().strip() in text
    assert "Куда написать" in text
    assert developer_urls(version=__version__)["release_tag"] in text


def test_developer_made_by_keyboard():
    kb = developer_made_by_keyboard(version="1.2.3")
    callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row if btn.callback_data]
    urls = [btn.url for row in kb.inline_keyboard for btn in row if btn.url]
    assert "menu:author" in callbacks
    assert developer_urls(version="1.2.3")["release_tag"] in urls
    labels = [btn.text for row in kb.inline_keyboard for btn in row]
    assert any("1.2.3" in t for t in labels)


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
    assert "баги" in footer
    assert developer_urls()["issues"] in footer
    assert "/author" in footer
    assert developer_urls()["release_tag"] in footer


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
        developer_urls()["release_tag"],
    }
    assert expected <= urls
    labels = [btn.text for row in kb.inline_keyboard for btn in row]
    assert "🆕 Что нового" in labels


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
