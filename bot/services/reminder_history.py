"""Журнал событий напоминаний — дневник и статистика."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder, ReminderEvent, ReminderEventKind
from bot.db.repository import async_session
from bot.services.user_prefs import format_snooze_minutes


@dataclass
class MonthStats:
    done: int = 0
    fired: int = 0
    snoozed: int = 0
    created: int = 0
    deleted: int = 0

    @property
    def completion_rate(self) -> int:
        if self.fired <= 0:
            return 0
        return min(100, round(self.done / self.fired * 100))


async def log_reminder_event(
    session: AsyncSession,
    *,
    reminder: Reminder | None,
    chat_id: int,
    user_telegram_id: int,
    text: str,
    kind: ReminderEventKind | str,
    event_at: datetime | None = None,
    extra: dict | None = None,
) -> ReminderEvent:
    event = ReminderEvent(
        reminder_id=reminder.id if reminder else None,
        chat_id=chat_id,
        user_telegram_id=user_telegram_id,
        reminder_text=text[:512],
        event_kind=str(kind),
        event_at=event_at or datetime.now().astimezone(),
        extra=json.dumps(extra, ensure_ascii=False) if extra else None,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


def _day_bounds(day: datetime, tz: ZoneInfo) -> tuple[datetime, datetime]:
    local = day.astimezone(tz)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def _month_bounds(day: datetime, tz: ZoneInfo) -> tuple[datetime, datetime]:
    local = day.astimezone(tz)
    start = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if local.month == 12:
        end = start.replace(year=local.year + 1, month=1)
    else:
        end = start.replace(month=local.month + 1)
    return start, end


async def get_day_events(
    session: AsyncSession,
    chat_id: int,
    *,
    day: datetime,
    timezone: str,
    user_telegram_id: int | None = None,
) -> list[ReminderEvent]:
    tz = ZoneInfo(timezone)
    start, end = _day_bounds(day, tz)
    query = (
        select(ReminderEvent)
        .where(
            ReminderEvent.chat_id == chat_id,
            ReminderEvent.event_at >= start,
            ReminderEvent.event_at < end,
        )
        .order_by(ReminderEvent.event_at.asc())
    )
    if user_telegram_id is not None:
        query = query.where(ReminderEvent.user_telegram_id == user_telegram_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_month_stats(
    session: AsyncSession,
    chat_id: int,
    *,
    day: datetime,
    timezone: str,
    user_telegram_id: int | None = None,
) -> MonthStats:
    tz = ZoneInfo(timezone)
    start, end = _month_bounds(day, tz)
    query = select(ReminderEvent.event_kind, func.count()).where(
        ReminderEvent.chat_id == chat_id,
        ReminderEvent.event_at >= start,
        ReminderEvent.event_at < end,
    )
    if user_telegram_id is not None:
        query = query.where(ReminderEvent.user_telegram_id == user_telegram_id)
    query = query.group_by(ReminderEvent.event_kind)
    result = await session.execute(query)
    stats = MonthStats()
    for kind, count in result.all():
        if kind == ReminderEventKind.DONE.value:
            stats.done = count
        elif kind == ReminderEventKind.FIRED.value:
            stats.fired = count
        elif kind == ReminderEventKind.SNOOZED.value:
            stats.snoozed = count
        elif kind == ReminderEventKind.CREATED.value:
            stats.created = count
        elif kind == ReminderEventKind.DELETED.value:
            stats.deleted = count
    return stats


async def get_inactive_reminders_for_day(
    session: AsyncSession,
    chat_id: int,
    *,
    day: datetime,
    timezone: str,
    user_telegram_id: int | None = None,
) -> list[Reminder]:
    tz = ZoneInfo(timezone)
    start, end = _day_bounds(day, tz)
    query = (
        select(Reminder)
        .where(
            Reminder.chat_id == chat_id,
            Reminder.is_active.is_(False),
            Reminder.created_at >= start,
            Reminder.created_at < end,
        )
        .order_by(Reminder.created_at.desc())
    )
    if user_telegram_id is not None:
        query = query.where(Reminder.created_by_telegram_id == user_telegram_id)
    result = await session.execute(query)
    return list(result.scalars().all())


def _event_icon(kind: str) -> str:
    return {
        ReminderEventKind.CREATED.value: "➕",
        ReminderEventKind.FIRED.value: "⏰",
        ReminderEventKind.SNOOZED.value: "⏱",
        ReminderEventKind.DONE.value: "✅",
        ReminderEventKind.DELETED.value: "🗑",
    }.get(kind, "•")


def _event_label(event: ReminderEvent, tz: ZoneInfo) -> str:
    time_str = event.event_at.astimezone(tz).strftime("%H:%M")
    icon = _event_icon(event.event_kind)
    rid = f" #{event.reminder_id}" if event.reminder_id else ""
    text = event.reminder_text
    if event.event_kind == ReminderEventKind.SNOOZED.value and event.extra:
        try:
            data = json.loads(event.extra)
            minutes = int(data.get("minutes", 0))
            if minutes:
                return f"{time_str} {icon} {text}{rid} (+{format_snooze_minutes(minutes)})"
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    if event.event_kind == ReminderEventKind.DONE.value:
        return f"{time_str} {icon} {text}{rid}"
    if event.event_kind == ReminderEventKind.FIRED.value:
        return f"{time_str} {icon} {text}{rid}"
    if event.event_kind == ReminderEventKind.CREATED.value:
        return f"{time_str} {icon} {text}{rid}"
    if event.event_kind == ReminderEventKind.DELETED.value:
        return f"{time_str} {icon} {text}{rid}"
    return f"{time_str} {icon} {text}{rid}"


def format_day_journal(
    events: list[ReminderEvent],
    *,
    timezone: str,
    day: datetime,
    active_count: int,
    planned_today: list[tuple[datetime, Reminder]],
) -> str:
    tz = ZoneInfo(timezone)
    date_label = day.astimezone(tz).strftime("%d.%m.%Y")
    lines = [f"📔 <b>Дневник</b> · {date_label}", ""]

    if not events and not planned_today:
        lines.append("Пока пусто — создай напоминание или дождись срабатывания.")
    else:
        if events:
            lines.append("<b>Сегодня</b>")
            for event in events:
                lines.append(_event_label(event, tz))
            lines.append("")

        if planned_today:
            lines.append("<b>Запланировано</b>")
            for run_at, reminder in planned_today:
                t = run_at.astimezone(tz).strftime("%H:%M")
                lines.append(f"{t} 🔜 {reminder.text} #{reminder.id}")

    done = sum(1 for e in events if e.event_kind == ReminderEventKind.DONE.value)
    fired = sum(1 for e in events if e.event_kind == ReminderEventKind.FIRED.value)
    lines.append("")
    lines.append(f"Активных: <b>{active_count}</b> · Срабатываний: <b>{fired}</b> · Готово: <b>{done}</b>")
    return "\n".join(lines)


def format_month_stats(stats: MonthStats, *, month_label: str) -> str:
    return (
        f"📊 <b>Статистика</b> · {month_label}\n\n"
        f"✅ Выполнено: <b>{stats.done}</b>\n"
        f"⏰ Срабатываний: <b>{stats.fired}</b>\n"
        f"⏱ Отложений: <b>{stats.snoozed}</b>\n"
        f"➕ Создано: <b>{stats.created}</b>\n"
        f"🗑 Удалено: <b>{stats.deleted}</b>\n"
        f"📈 Выполнение: <b>{stats.completion_rate}%</b>"
    )


async def get_planned_for_day(
    session: AsyncSession,
    chat_id: int,
    *,
    day: datetime,
    timezone: str,
) -> list[tuple[datetime, Reminder]]:
    tz = ZoneInfo(timezone)
    start, end = _day_bounds(day, tz)
    result = await session.execute(
        select(Reminder).where(
            Reminder.chat_id == chat_id,
            Reminder.is_active.is_(True),
            Reminder.next_run_at.is_not(None),
            Reminder.next_run_at >= start,
            Reminder.next_run_at < end,
        ).order_by(Reminder.next_run_at.asc())
    )
    items: list[tuple[datetime, Reminder]] = []
    for reminder in result.scalars().all():
        if reminder.next_run_at is not None:
            items.append((reminder.next_run_at, reminder))
    return items


async def build_journal_message(chat_id: int, user_telegram_id: int, timezone: str) -> str:
    now = datetime.now(ZoneInfo(timezone))
    async with async_session() as session:
        from bot.db.repository import get_active_chat_reminders

        events = await get_day_events(
            session, chat_id, day=now, timezone=timezone, user_telegram_id=user_telegram_id
        )
        planned = await get_planned_for_day(session, chat_id, day=now, timezone=timezone)
        active = await get_active_chat_reminders(session, chat_id)
    return format_day_journal(
        events,
        timezone=timezone,
        day=now,
        active_count=len(active),
        planned_today=planned,
    )


async def build_stats_message(chat_id: int, user_telegram_id: int, timezone: str) -> str:
    now = datetime.now(ZoneInfo(timezone))
    month_label = now.astimezone(ZoneInfo(timezone)).strftime("%B %Y")
    # Russian month names simple mapping
    months_ru = {
        "January": "январь", "February": "февраль", "March": "март", "April": "апрель",
        "May": "май", "June": "июнь", "July": "июль", "August": "август",
        "September": "сентябрь", "October": "октябрь", "November": "ноябрь", "December": "декабрь",
    }
    for en, ru in months_ru.items():
        month_label = month_label.replace(en, ru)
    async with async_session() as session:
        stats = await get_month_stats(
            session, chat_id, day=now, timezone=timezone, user_telegram_id=user_telegram_id
        )
    return format_month_stats(stats, month_label=month_label)
