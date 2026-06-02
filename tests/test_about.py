from bot.texts.messages import format_about, DEVELOPER_GITHUB_REPO, DEVELOPER_TELEGRAM
from bot.version import __version__
from bot.keyboards.inline import about_developer_keyboard


def test_format_about_contains_version():
    text = format_about(__version__)
    assert __version__ in text
    assert "Дневник" in text
    assert "Статистика" in text


def test_format_about_developer_links():
    text = format_about(__version__)
    assert "Разработчик" in text
    assert f"@{DEVELOPER_TELEGRAM}" in text
    assert DEVELOPER_GITHUB_REPO in text
    assert f"https://t.me/{DEVELOPER_TELEGRAM}" in text
    assert f"https://github.com/{DEVELOPER_GITHUB_REPO}" in text


def test_about_developer_keyboard_urls():
    kb = about_developer_keyboard()
    urls = [btn.url for row in kb.inline_keyboard for btn in row if btn.url]
    assert f"https://t.me/{DEVELOPER_TELEGRAM}" in urls
    assert f"https://github.com/{DEVELOPER_GITHUB_REPO}" in urls
