from datetime import datetime
from zoneinfo import ZoneInfo

from bot.services.date_format import format_month_year


def test_format_month_year():
    dt = datetime(2026, 5, 15, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))
    assert format_month_year(dt) == "Май 2026"
