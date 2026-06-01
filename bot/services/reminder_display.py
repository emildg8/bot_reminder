"""Форматирование напоминаний для списка и UI."""

from datetime import datetime
from html import escape

from zoneinfo import ZoneInfo

from bot.db.models import Reminder
from bot.services.nlp.schemas import ParsedReminder
from bot.texts.messages import format_delay_label
from bot.services.reminder_utils import compute_next_run, local_run_at, mask_to_weekdays
from bot.services.timezone_labels import format_timezone_label

WEEKDAY_NAMES = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

KIND_ICONS = {
    "once": "⏱",
    "interval": "🔁",
    "daily": "📅",
    "weekly": "📆",
}

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
    names = [WEEKDAY_NAMES[d] for d in sorted(wd)]
    return ", ".join(names) if len(names) > 2 else " ".join(names)


def format_parsed_when_label(parsed: ParsedReminder, timezone: str) -> str:
    """Краткая подпись расписания для сообщений «создано» / «обновлено»."""
    tz = ZoneInfo(timezone)
    if parsed.kind == "once" and parsed.delay_seconds:
        return format_delay_label(parsed.delay_seconds)
    if parsed.kind == "weekly" and parsed.daily_time and parsed.weekdays:
        days = format_weekdays_label(weekdays=parsed.weekdays)
        return f"{days} в {parsed.daily_time.strftime('%H:%M')}"
    if parsed.kind == "daily" and parsed.daily_time:
        return f"ежедневно в {parsed.daily_time.strftime('%H:%M')}"
    if parsed.kind == "interval":
        nxt = compute_next_run(parsed, timezone).astimezone(tz)
        base = format_interval_seconds(parsed.interval_seconds)
        return f"{base}, след. {nxt.strftime('%d.%m %H:%M')}"
    if parsed.run_at:
        return parsed.run_at.astimezone(tz).strftime("%d.%m.%Y %H:%M")
    return compute_next_run(parsed, timezone).astimezone(tz).strftime("%d.%m.%Y %H:%M")


def format_reminder_schedule(reminder: Reminder, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    next_run = local_run_at(reminder.next_run_at, reminder.timezone)
    if reminder.kind == "once" and next_run:
        nxt = next_run.astimezone(tz)
        if nxt <= now:
            return f"✅ сработало {nxt.strftime('%d.%m %H:%M')}"
    if reminder.kind == "interval" and reminder.interval_seconds:
        if next_run:
            nxt = next_run.astimezone(tz).strftime("%d.%m %H:%M")
            return f"{format_interval_seconds(reminder.interval_seconds)}, след. {nxt}"
        return format_interval_seconds(reminder.interval_seconds)

    if reminder.kind == "daily" and reminder.daily_time:
        return f"ежедневно {reminder.daily_time.strftime('%H:%M')}"

    if reminder.kind == "weekly" and reminder.daily_time:
        days = format_weekdays_label(mask=reminder.weekdays_mask)
        t = reminder.daily_time.strftime("%H:%M")
        return f"{days} в {t}" if days else f"в {t}"

    if next_run:
        return next_run.astimezone(tz).strftime("%d.%m.%Y %H:%M")

    if reminder.daily_time:
        return reminder.daily_time.strftime("%H:%M")

    return "—"


def format_reminder_list_line(reminder: Reminder, timezone: str | None = None) -> str:
    tz_name = timezone or reminder.timezone
    icon = KIND_ICONS.get(reminder.kind, "📌")
    kind = KIND_LABELS.get(reminder.kind, reminder.kind)
    when = format_reminder_schedule(reminder, tz_name)
    mention = " 👤"
    if reminder.mention_telegram_id:
        mention = f' <a href="tg://user?id={reminder.mention_telegram_id}">👤</a>'
    text = escape(reminder.text)
    if len(reminder.text) > 70:
        text = escape(reminder.text[:67]) + "…"
    return f"{icon} <b>#{reminder.id}</b> · {kind} · {when}\n   {text}{mention}"


def format_parsed_summary_html(parsed: ParsedReminder, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    next_run = compute_next_run(parsed, timezone).astimezone(tz)
    icon = KIND_ICONS.get(parsed.kind, "📌")
    kind = KIND_LABELS.get(parsed.kind, parsed.kind)
    tz_label = format_timezone_label(timezone)

    when_line = ""
    if parsed.kind == "once":
        if parsed.delay_seconds:
            when_line = format_delay_label(parsed.delay_seconds)
        else:
            when_line = next_run.strftime("%d.%m.%Y %H:%M")
    elif parsed.kind == "interval":
        when_line = format_interval_seconds(parsed.interval_seconds)
        when_line += f", первый раз {next_run.strftime('%d.%m %H:%M')}"
    elif parsed.kind == "daily" and parsed.daily_time:
        when_line = f"ежедневно в {parsed.daily_time.strftime('%H:%M')}"
    elif parsed.kind == "weekly" and parsed.daily_time and parsed.weekdays:
        days = format_weekdays_label(weekdays=parsed.weekdays)
        when_line = f"{days} в {parsed.daily_time.strftime('%H:%M')}"
    else:
        when_line = next_run.strftime("%d.%m.%Y %H:%M")

    return (
        f"{icon} <b>{kind.capitalize()}</b>\n"
        f"🕐 {when_line}\n"
        f"📝 {escape(parsed.text)}\n"
        f"🌍 {tz_label}"
    )


def format_batch_parsed_summary_html(items: list[ParsedReminder], timezone: str) -> str:
    if len(items) == 1:
        return format_parsed_summary_html(items[0], timezone)

    weekly_batch = all(p.kind == "weekly" for p in items)
    header = (
        f"📋 <b>{len(items)} еженедельных напоминания</b> (по одному на время)\n"
        if weekly_batch
        else f"📋 <b>{len(items)} напоминания</b>\n"
    )
    lines = [header]
    for parsed in items:
        if parsed.kind == "weekly" and parsed.daily_time and parsed.weekdays:
            days = format_weekdays_label(weekdays=parsed.weekdays)
            when = f"{days} в {parsed.daily_time.strftime('%H:%M')}"
        elif parsed.kind == "once" and parsed.delay_seconds:
            when = format_delay_label(parsed.delay_seconds)
        elif parsed.kind == "once" and parsed.run_at:
            when = parsed.run_at.astimezone(ZoneInfo(timezone)).strftime("%d.%m.%Y %H:%M")
        else:
            when = format_parsed_summary_html(parsed, timezone).split("\n")[1].removeprefix("🕐 ")
        lines.append(f"• {when} — {escape(parsed.text)}")
    lines.append(f"\n🌍 {format_timezone_label(timezone)}")
    return "\n".join(lines)


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
