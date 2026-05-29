"""Форматирование напоминаний для списка и UI."""

from zoneinfo import ZoneInfo

from bot.db.models import Reminder
from bot.services.reminder_utils import mask_to_weekdays

WEEKDAY_NAMES = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

KIND_LABELS = {
    "once": "разово",
    "interval": "интервал",
    "daily": "ежедневно",
    "weekly": "по дням",
}


def format_interval_seconds(seconds: int | None) -> str:
    if not seconds:
        return "интервал"
    if seconds % 3600 == 0:
        h = seconds // 3600
        return f"каждые {h} ч."
    if seconds % 60 == 0:
        m = seconds // 60
        return f"каждые {m} мин."
    return f"каждые {seconds} сек."


def format_weekdays_label(weekdays: list[int] | None = None, mask: int | None = None) -> str:
    if mask is not None:
        weekdays = mask_to_weekdays(mask)
    if not weekdays:
        return ""
    wd = set(weekdays)
    if wd == {0, 1, 2, 3, 4}:
        return "по будням"
    if wd == {5, 6}:
        return "по выходным"
    return " ".join(WEEKDAY_NAMES[d] for d in sorted(wd))


def format_reminder_schedule(reminder: Reminder, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    if reminder.kind == "interval" and reminder.interval_seconds:
        if reminder.next_run_at:
            nxt = reminder.next_run_at.astimezone(tz).strftime("%d.%m %H:%M")
            return f"{format_interval_seconds(reminder.interval_seconds)}, след. {nxt}"
        return format_interval_seconds(reminder.interval_seconds)

    if reminder.kind == "daily" and reminder.daily_time:
        return f"ежедневно {reminder.daily_time.strftime('%H:%M')}"

    if reminder.kind == "weekly" and reminder.daily_time:
        days = format_weekdays_label(mask=reminder.weekdays_mask)
        t = reminder.daily_time.strftime("%H:%M")
        return f"{days} в {t}" if days else f"в {t}"

    if reminder.next_run_at:
        return reminder.next_run_at.astimezone(tz).strftime("%d.%m.%Y %H:%M")

    if reminder.daily_time:
        return reminder.daily_time.strftime("%H:%M")

    return "—"


def format_reminder_list_line(reminder: Reminder, timezone: str | None = None) -> str:
    tz_name = timezone or reminder.timezone
    kind = KIND_LABELS.get(reminder.kind, reminder.kind)
    when = format_reminder_schedule(reminder, tz_name)
    mention = " 👤" if reminder.mention_telegram_id else ""
    text = reminder.text
    if len(text) > 80:
        text = text[:77] + "…"
    return f"#{reminder.id} [{kind}] {when} — {text}{mention}"


def reminder_to_export_dict(reminder: Reminder) -> dict:
    return {
        "id": reminder.id,
        "chat_id": reminder.chat_id,
        "created_by_telegram_id": reminder.created_by_telegram_id,
        "mention_telegram_id": reminder.mention_telegram_id,
        "timezone": reminder.timezone,
        "text": reminder.text,
        "kind": reminder.kind,
        "next_run_at": reminder.next_run_at.isoformat() if reminder.next_run_at else None,
        "interval_seconds": reminder.interval_seconds,
        "daily_time": reminder.daily_time.strftime("%H:%M") if reminder.daily_time else None,
        "weekdays_mask": reminder.weekdays_mask,
        "is_active": reminder.is_active,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
    }
