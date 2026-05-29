"""Парсинг элементов JSON-экспорта для импорта."""

from dataclasses import dataclass
from datetime import datetime, time

from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_utils import compute_next_run, mask_to_weekdays


@dataclass
class ImportResult:
    parsed: ParsedReminder
    timezone: str
    mention_telegram_id: int | None
    weekdays_mask: int | None


def parse_import_item(item: dict, default_timezone: str) -> ImportResult:
    kind = item.get("kind", "once")
    text_val = str(item.get("text", "")).strip()
    if not text_val:
        raise ValueError("пустой текст")

    tz = item.get("timezone") or default_timezone
    daily_time = None
    if item.get("daily_time"):
        h, m = str(item["daily_time"]).split(":")
        daily_time = time(int(h), int(m))

    weekdays_mask = item.get("weekdays_mask")
    weekdays_list = mask_to_weekdays(weekdays_mask) if weekdays_mask else None

    next_run_at = None
    if item.get("next_run_at"):
        next_run_at = datetime.fromisoformat(str(item["next_run_at"]).replace("Z", "+00:00"))

    mention_raw = item.get("mention_telegram_id")
    mention_telegram_id = int(mention_raw) if mention_raw is not None else None

    parsed = ParsedReminder(
        text=text_val,
        kind=kind,
        run_at=next_run_at,
        interval_seconds=item.get("interval_seconds"),
        daily_time=daily_time,
        weekdays=weekdays_list,
    )
    compute_next_run(parsed, tz)

    return ImportResult(
        parsed=parsed,
        timezone=tz,
        mention_telegram_id=mention_telegram_id,
        weekdays_mask=weekdays_mask,
    )
