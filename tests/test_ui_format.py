from datetime import datetime, time

from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_display import format_parsed_summary_html


def test_parsed_summary_html():
    parsed = ParsedReminder(
        text="зарядка",
        kind="daily",
        daily_time=time(9, 0),
    )
    html = format_parsed_summary_html(parsed, "Europe/Moscow")
    assert "зарядка" in html
    assert "09:00" in html
    assert "Москва" in html
