#!/usr/bin/env python3
"""Smoke author-presence: тексты и клавиатуры (без pytest).

Запуск: python scripts/smoke_author.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.keyboards.inline import developer_links_keyboard, developer_made_by_keyboard  # noqa: E402
from bot.services.stars_tips import tip_thank_you_keyboard  # noqa: E402
from bot.texts.messages import (  # noqa: E402
    DEVELOPER_TELEGRAM,
    developer_urls,
    format_developer_card,
    format_developer_made_by_line,
    format_developer_status_line,
    format_developer_teaser,
    format_help_feedback_footer,
)
from bot.version import __version__


def _ok(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    errors: list[str] = []
    ver = __version__
    urls = developer_urls(version=ver)

    _ok(DEVELOPER_TELEGRAM in format_developer_made_by_line(), "made_by line", errors)
    _ok("/author" in format_developer_teaser(version=ver), "teaser /author", errors)
    _ok(urls["release_tag"] in format_developer_status_line(version=ver), "status release_tag", errors)
    _ok(DEVELOPER_TELEGRAM in format_developer_card(version=ver), "card author", errors)
    _ok(urls["release_tag"] in format_help_feedback_footer(), "help footer release", errors)

    made_by = developer_made_by_keyboard(version=ver)
    callbacks = [b.callback_data for row in made_by.inline_keyboard for b in row if b.callback_data]
    _ok("menu:author" in callbacks, "made_by keyboard author", errors)

    links = developer_links_keyboard(include_thanks=False, version=ver)
    link_urls = {b.url for row in links.inline_keyboard for b in row if b.url}
    _ok(urls["release_tag"] in link_urls, "links release_tag", errors)

    thanks = tip_thank_you_keyboard()
    thanks_cb = [b.callback_data for row in thanks.inline_keyboard for b in row if b.callback_data]
    _ok("menu:author" in thanks_cb and "menu:thanks" in thanks_cb, "thank_you keyboard", errors)

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("smoke_author OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
