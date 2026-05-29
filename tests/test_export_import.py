from datetime import time

import pytest

from bot.services.export_import import parse_import_item


def test_parse_import_with_mention():
    item = {
        "text": "задача",
        "kind": "daily",
        "daily_time": "09:00",
        "timezone": "Europe/Moscow",
        "mention_telegram_id": 12345,
        "is_active": True,
    }
    result = parse_import_item(item, "Europe/Moscow")
    assert result.parsed.text == "задача"
    assert result.mention_telegram_id == 12345
    assert result.parsed.daily_time == time(9, 0)


def test_parse_import_empty_text_raises():
    with pytest.raises(ValueError, match="пустой"):
        parse_import_item({"text": "  ", "kind": "once"}, "Europe/Moscow")
