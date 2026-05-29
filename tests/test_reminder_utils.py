from datetime import time

from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import compute_next_run, mask_to_weekdays, weekdays_to_mask


def test_weekdays_mask_roundtrip():
    mask = weekdays_to_mask([0, 2, 4])
    assert mask_to_weekdays(mask) == [0, 2, 4]


def test_compute_next_run_daily():
    parsed = ParsedReminder(
        text="зарядка",
        kind="daily",
        daily_time=time(9, 0),
    )
    next_run = compute_next_run(parsed, "Europe/Moscow")
    assert next_run.hour == 9
    assert next_run.minute == 0
