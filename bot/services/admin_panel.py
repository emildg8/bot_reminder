"""Панель администратора и вспомогательные операции."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from html import escape

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import String, cast, distinct, func, select

from bot.config import settings
from bot.db.models import Reminder, User
from bot.db.repository import (
    async_session,
    count_active_reminders_for_user,
    count_user_star_tips,
    delete_broadcast_draft,
    get_broadcast_draft,
    get_star_tips_summary,
    get_user_by_telegram_id,
    upsert_broadcast_draft,
)
from bot.services.admin_access import get_admin_tools_enabled, is_admin_listed, is_bot_admin
from bot.services.stars_tips import tips_enabled
from bot.services.timezone_labels import format_timezone_label
from bot.version import __version__

logger = logging.getLogger(__name__)

BROADCAST_MAX_RECIPIENTS = 100
BROADCAST_DELAY_SEC = 0.05

_FILTER_ALIASES: dict[str, str] = {
    "all": "all",
    "все": "all",
    "active": "active",
    "активные": "active",
    "актив": "active",
    "pro": "pro",
    "free": "free",
    "бесплатные": "free",
    "бесплат": "free",
}

_FILTER_LABELS: dict[str, str] = {
    "all": "все пользователи",
    "active": "с активными напоминаниями",
    "pro": "Pro",
    "free": "Free",
}


class BroadcastFilter(str, Enum):
    ALL = "all"
    ACTIVE = "active"
    PRO = "pro"
    FREE = "free"


@dataclass
class PendingBroadcast:
    text: str
    filter: BroadcastFilter = BroadcastFilter.ALL


@dataclass
class BroadcastArgs:
    action: str  # preview | send | test | help
    filter: BroadcastFilter
    text: str


def is_userinfo_card(text: str | None) -> bool:
    return bool(text and "Пользователь" in text)


async def build_userinfo_reply(telegram_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    text = await format_user_info(telegram_id)
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user is None:
            return text, None
        active = await count_active_reminders_for_user(session, telegram_id)
    kb = user_info_keyboard(telegram_id, active_count=active)
    return text, kb


def userfind_keyboard(ids: list[int]) -> InlineKeyboardMarkup | None:
    if not ids:
        return None
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for tid in ids:
        label = str(tid)
        if len(label) > 10:
            label = "…" + label[-8:]
        row.append(
            InlineKeyboardButton(text=label, callback_data=f"admin:userinfo:{tid}")
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


BROADCAST_HELP = (
    "Формат:\n"
    "• <code>/broadcast Текст</code> — превью\n"
    "• <code>/broadcast активные Текст</code> · <code>pro</code> · <code>free</code>\n"
    "• <code>/broadcast test Текст</code> — пример себе\n"
    "• <code>/broadcast да Текст</code> — сразу (до 100)"
)


def parse_target_telegram_id(message: Message) -> int | None:
    """ID из аргумента команды или из сообщения, на которое ответили."""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) >= 2:
        try:
            return int(parts[1].strip())
        except ValueError:
            return None
    reply = message.reply_to_message
    if reply and reply.from_user and not reply.from_user.is_bot:
        return reply.from_user.id
    return None


def parse_broadcast_message(message: Message) -> BroadcastArgs | None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return None
    rest = parts[1].strip()
    if not rest:
        return None

    tokens = rest.split()
    action = "preview"
    filt = BroadcastFilter.ALL
    idx = 0

    while idx < len(tokens):
        word = tokens[idx].lower()
        if word in ("да", "yes", "confirm"):
            action = "send"
            idx += 1
            continue
        if word in ("test", "себе", "self"):
            action = "test"
            idx += 1
            continue
        if word in _FILTER_ALIASES:
            filt = BroadcastFilter(_FILTER_ALIASES[word])
            idx += 1
            continue
        break

    text = " ".join(tokens[idx:]).strip()
    if not text:
        return BroadcastArgs(action="help", filter=filt, text="")
    return BroadcastArgs(action=action, filter=filt, text=text)


async def set_pending_broadcast(
    admin_id: int, text: str, *, filter: BroadcastFilter = BroadcastFilter.ALL
) -> None:
    async with async_session() as session:
        await upsert_broadcast_draft(session, admin_id, text, filter=filter.value)


async def pop_pending_broadcast(admin_id: int) -> PendingBroadcast | None:
    async with async_session() as session:
        draft = await get_broadcast_draft(session, admin_id)
        if draft is None:
            return None
        await delete_broadcast_draft(session, admin_id)
        try:
            filt = BroadcastFilter(draft.filter)
        except ValueError:
            filt = BroadcastFilter.ALL
        return PendingBroadcast(text=draft.text, filter=filt)


async def get_pending_broadcast(admin_id: int) -> PendingBroadcast | None:
    async with async_session() as session:
        draft = await get_broadcast_draft(session, admin_id)
        if draft is None:
            return None
        try:
            filt = BroadcastFilter(draft.filter)
        except ValueError:
            filt = BroadcastFilter.ALL
        return PendingBroadcast(text=draft.text, filter=filt)


async def count_broadcast_recipients(filter: BroadcastFilter = BroadcastFilter.ALL) -> int:
    async with async_session() as session:
        if filter == BroadcastFilter.ALL:
            return (
                await session.execute(select(func.count()).select_from(User))
            ).scalar_one()
        if filter == BroadcastFilter.ACTIVE:
            result = await session.execute(
                select(func.count(distinct(Reminder.created_by_telegram_id))).where(
                    Reminder.is_active.is_(True)
                )
            )
            return result.scalar_one()
        if filter == BroadcastFilter.PRO:
            return (
                await session.execute(
                    select(func.count()).select_from(User).where(User.is_pro.is_(True))
                )
            ).scalar_one()
        return (
            await session.execute(
                select(func.count()).select_from(User).where(User.is_pro.is_(False))
            )
        ).scalar_one()


async def _select_broadcast_recipient_ids(
    filter: BroadcastFilter,
    *,
    limit: int,
) -> list[int]:
    async with async_session() as session:
        if filter == BroadcastFilter.ALL:
            result = await session.execute(
                select(User.telegram_id).order_by(User.id.desc()).limit(limit)
            )
            return list(result.scalars().all())

        if filter == BroadcastFilter.ACTIVE:
            subq = (
                select(Reminder.created_by_telegram_id)
                .where(Reminder.is_active.is_(True))
                .distinct()
            )
            result = await session.execute(subq.limit(limit))
            return list(result.scalars().all())

        if filter == BroadcastFilter.PRO:
            result = await session.execute(
                select(User.telegram_id)
                .where(User.is_pro.is_(True))
                .order_by(User.id.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        # FREE — в БД без Pro (админы с bypass не попадают в рассылку «free»)
        result = await session.execute(
            select(User.telegram_id)
            .where(User.is_pro.is_(False))
            .order_by(User.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def format_quick_stats() -> str:
    from bot.services.scheduler import count_scheduled_reminder_jobs

    async with async_session() as session:
        users = (
            await session.execute(select(func.count()).select_from(User))
        ).scalar_one()
        active_reminders = (
            await session.execute(
                select(func.count()).select_from(Reminder).where(Reminder.is_active.is_(True))
            )
        ).scalar_one()
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        new_week = (
            await session.execute(
                select(func.count()).select_from(User).where(User.created_at >= week_ago)
            )
        ).scalar_one()
        with_active = (
            await session.execute(
                select(func.count(distinct(Reminder.created_by_telegram_id))).where(
                    Reminder.is_active.is_(True)
                )
            )
        ).scalar_one()

    jobs = count_scheduled_reminder_jobs()
    lines = [
        f"👥 {users} польз. · 📋 {active_reminders} активных",
        f"👤 с напоминаниями: <b>{with_active}</b> · ⏱ в планировщике: <b>{jobs}</b>",
        f"🆕 за 7 дней: <b>{new_week}</b>",
    ]
    if tips_enabled():
        async with async_session() as session:
            tip_count, tip_total = await get_star_tips_summary(session)
        lines.append(f"⭐ Stars: <b>{tip_count}</b> · сумма <b>{tip_total}</b>")
    return "\n".join(lines)


async def format_admin_panel_intro() -> str:
    stats = await format_quick_stats()
    return (
        f"🎛 <b>Панель администратора</b> · v{__version__}\n"
        f"{stats}\n\n"
        "Кнопки ниже или команды:\n"
        "• <code>/userinfo ID</code> или <b>ответ</b> + /userinfo\n"
        "• <code>/broadcast текст</code> — превью\n"
        "• фильтры: <code>активные</code> · <code>pro</code> · <code>free</code>\n"
        "• <code>/broadcast test текст</code> — пример себе\n"
        f"• <code>/broadcast да текст</code> — сразу (до {BROADCAST_MAX_RECIPIENTS})\n"
        "• <code>/userfind 123</code> — поиск ID · <code>/adminlog</code> · <code>/adminstats</code>"
    )


def format_admin_panel_limited() -> str:
    return (
        "🎛 <b>Панель</b> (режим пользователя)\n\n"
        "Команды ops скрыты. Включи <b>🛠 режим администратора</b> для Health, "
        "рассылки и userinfo."
    )


def admin_limited_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛠 Режим администратора",
                    callback_data="adminmode:admin",
                )
            ],
            [
                InlineKeyboardButton(text="🛠 /adminmode", callback_data="admin:run:adminmode"),
            ],
        ]
    )


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏥 Health", callback_data="adminmode:cmd:health"),
                InlineKeyboardButton(text="📈 Sysinfo", callback_data="adminmode:cmd:sysinfo"),
            ],
            [
                InlineKeyboardButton(text="👤 Userinfo", callback_data="admin:hint:userinfo"),
                InlineKeyboardButton(text="🕐 Недавние", callback_data="admin:run:recent"),
            ],
            [
                InlineKeyboardButton(text="👥 Admins", callback_data="admin:run:admins"),
                InlineKeyboardButton(text="⬆️ Update", callback_data="adminmode:cmd:update"),
            ],
            [
                InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:hint:broadcast"),
                InlineKeyboardButton(text="📊 Stats", callback_data="admin:run:stats"),
            ],
            [
                InlineKeyboardButton(text="📜 Лог", callback_data="admin:run:log"),
                InlineKeyboardButton(text="🔍 Find", callback_data="admin:hint:find"),
            ],
            [
                InlineKeyboardButton(text="🛠 /adminmode", callback_data="admin:run:adminmode"),
                InlineKeyboardButton(text="👤 User-mode", callback_data="adminmode:user"),
            ],
        ]
    )


def user_info_keyboard(target_id: int, *, active_count: int = 0) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=f"admin:userinfo:{target_id}",
            )
        ],
    ]
    if active_count > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📋 Напоминания",
                    callback_data=f"admin:reminders:{target_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _filter_button_label(name: str, filt: BroadcastFilter, current: BroadcastFilter) -> str:
    prefix = "✓ " if filt == current else ""
    return prefix + name


def broadcast_preview_keyboard(*, current: BroadcastFilter = BroadcastFilter.ALL) -> InlineKeyboardMarkup:
    filter_row = [
        InlineKeyboardButton(
            text=_filter_button_label("Все", BroadcastFilter.ALL, current),
            callback_data="admin:bcast:filter:all",
        ),
        InlineKeyboardButton(
            text=_filter_button_label("Активн.", BroadcastFilter.ACTIVE, current),
            callback_data="admin:bcast:filter:active",
        ),
        InlineKeyboardButton(
            text=_filter_button_label("Pro", BroadcastFilter.PRO, current),
            callback_data="admin:bcast:filter:pro",
        ),
        InlineKeyboardButton(
            text=_filter_button_label("Free", BroadcastFilter.FREE, current),
            callback_data="admin:bcast:filter:free",
        ),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            filter_row,
            [
                InlineKeyboardButton(text="📨 Себе", callback_data="admin:bcast:self"),
                InlineKeyboardButton(text="✅ Отправить", callback_data="admin:bcast:confirm"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:bcast:cancel")],
        ]
    )


async def format_user_info(telegram_id: int) -> str:
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user is None:
            return f"❌ Пользователь <code>{telegram_id}</code> не найден в БД."
        active = await count_active_reminders_for_user(session, telegram_id)
        total_q = await session.execute(
            select(func.count())
            .select_from(Reminder)
            .where(Reminder.created_by_telegram_id == telegram_id)
        )
        total = total_q.scalar_one()
        chats_q = await session.execute(
            select(func.count(distinct(Reminder.chat_id)))
            .where(
                Reminder.created_by_telegram_id == telegram_id,
                Reminder.is_active.is_(True),
            )
        )
        chat_count = chats_q.scalar_one()
        next_row = await session.execute(
            select(Reminder.text, Reminder.next_run_at)
            .where(
                Reminder.created_by_telegram_id == telegram_id,
                Reminder.is_active.is_(True),
                Reminder.next_run_at.isnot(None),
            )
            .order_by(Reminder.next_run_at.asc())
            .limit(1)
        )
        next_reminder = next_row.first()
        tip_count, tip_total = await count_user_star_tips(session, telegram_id)

    lines = [
        f"👤 <b>Пользователь</b> <code>{telegram_id}</code>",
        f"🕐 Часовой пояс: <b>{format_timezone_label(user.timezone)}</b>"
        + (" ✓" if user.timezone_confirmed else " (не подтверждён)"),
        f"📋 Активных: <b>{active}</b> · всего: <b>{total}</b> · чатов: <b>{chat_count}</b>",
    ]
    if next_reminder:
        ntext, nrun = next_reminder
        when = nrun.strftime("%d.%m %H:%M") if nrun else "?"
        short = escape((ntext or "")[:60]) + ("…" if len(ntext or "") > 60 else "")
        lines.append(f"⏭ Ближайшее: <b>{when}</b> — {short}")
    if tip_count:
        lines.append(f"⭐ Stars: <b>{tip_count}</b> · сумма <b>{tip_total}</b>")
    if is_admin_listed(telegram_id):
        mode = "администратор" if user.admin_tools_enabled else "пользователь (тест)"
        lines.append(f"🛠 Админ бота: <b>{mode}</b>")
    if user.onboarding_done:
        lines.append("✅ Онбординг пройден")
    created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "—"
    lines.append(f"📅 В БД с: <code>{created}</code>")
    return "\n".join(lines)


async def format_user_reminders(telegram_id: int, limit: int = 5) -> str:
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, telegram_id)
        if user is None:
            return f"❌ Пользователь <code>{telegram_id}</code> не найден."
        result = await session.execute(
            select(Reminder.text, Reminder.next_run_at, Reminder.chat_id)
            .where(
                Reminder.created_by_telegram_id == telegram_id,
                Reminder.is_active.is_(True),
            )
            .order_by(Reminder.next_run_at.asc().nulls_last())
            .limit(limit)
        )
        rows = list(result.all())

    if not rows:
        return f"📋 У <code>{telegram_id}</code> нет активных напоминаний."

    lines = [f"📋 <b>Активные напоминания</b> · <code>{telegram_id}</code>\n"]
    for text, nrun, chat_id in rows:
        when = nrun.strftime("%d.%m %H:%M") if nrun else "—"
        short = escape((text or "")[:50]) + ("…" if len(text or "") > 50 else "")
        lines.append(f"• <b>{when}</b> · chat <code>{chat_id}</code>\n  {short}")
    return "\n".join(lines)


@dataclass
class RecentUserRow:
    telegram_id: int
    created_at: datetime | None
    active_count: int


async def fetch_recent_users(limit: int = 8) -> list[RecentUserRow]:
    async with async_session() as session:
        result = await session.execute(
            select(User.telegram_id, User.created_at)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        rows = list(result.all())
        out: list[RecentUserRow] = []
        for tid, created in rows:
            active = await count_active_reminders_for_user(session, tid)
            out.append(RecentUserRow(tid, created, active))
        return out


async def format_recent_users(limit: int = 8) -> str:
    rows = await fetch_recent_users(limit)
    if not rows:
        return "В БД пока нет пользователей."
    lines = ["🕐 <b>Недавние пользователи</b> (нажми кнопку или /userinfo ID)\n"]
    for row in rows:
        when = row.created_at.strftime("%d.%m.%Y") if row.created_at else "?"
        act = f" · <b>{row.active_count}</b> акт." if row.active_count else ""
        lines.append(f"• <code>{row.telegram_id}</code> — {when}{act}")
    return "\n".join(lines)


async def find_users_by_id_fragment(fragment: str, *, limit: int = 10) -> list[int]:
    fragment = fragment.strip()
    if not fragment.isdigit() or len(fragment) < 3:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(User.telegram_id)
            .where(cast(User.telegram_id, String).like(f"%{fragment}%"))
            .order_by(User.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def format_userfind_results(fragment: str) -> tuple[str, InlineKeyboardMarkup | None]:
    ids = await find_users_by_id_fragment(fragment)
    if not ids:
        return (
            f"🔍 По фрагменту <code>{escape(fragment)}</code> ничего не найдено.\n"
            "Нужно минимум 3 цифры · <code>/userfind 123456789</code>",
            None,
        )
    lines = [f"🔍 <b>Найдено</b> ({len(ids)}):\n"]
    for tid in ids:
        lines.append(f"• <code>{tid}</code>")
    return "\n".join(lines), userfind_keyboard(ids)


async def format_admin_stats() -> str:
    from bot.services.scheduler import count_scheduled_reminder_jobs

    stats = await format_quick_stats()
    async with async_session() as session:
        kinds = await session.execute(
            select(Reminder.kind, func.count())
            .where(Reminder.is_active.is_(True))
            .group_by(Reminder.kind)
        )
        kind_rows = list(kinds.all())
        groups = await session.execute(
            select(func.count(distinct(Reminder.chat_id))).where(Reminder.is_active.is_(True))
        )
        group_chats = groups.scalar_one()

    kind_lines = " · ".join(f"{k}: <b>{n}</b>" for k, n in kind_rows) if kind_rows else "—"
    jobs = count_scheduled_reminder_jobs()
    return (
        "📊 <b>Статистика бота</b>\n\n"
        f"{stats}\n\n"
        f"💬 Групповых чатов с активными: <b>{group_chats}</b>\n"
        f"📋 По типам (активные): {kind_lines}\n"
        f"⏱ Задач планировщика: <b>{jobs}</b>"
    )


def recent_users_keyboard(rows: list[RecentUserRow]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for entry in rows:
        label = str(entry.telegram_id)
        if len(label) > 10:
            label = "…" + label[-8:]
        if entry.active_count:
            label = f"{label}({entry.active_count})"
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"admin:userinfo:{entry.telegram_id}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def format_admins_list(caller_id: int | None = None) -> str:
    if not settings.admin_telegram_ids:
        return "Список <code>ADMIN_TELEGRAM_IDS</code> пуст."
    lines = ["👥 <b>Администраторы бота</b>\n"]
    async with async_session() as session:
        for aid in settings.admin_telegram_ids:
            tools = await get_admin_tools_enabled(session, aid)
            mode = "🛠 admin" if tools else "👤 user-test"
            suffix = " ← ты" if caller_id is not None and aid == caller_id else ""
            cache_tools = is_bot_admin(aid)
            lines.append(f"• <code>{aid}</code> — {mode}{suffix}")
            if tools != cache_tools:
                lines.append("  ⚠️ кэш ≠ БД — /adminmode или рестарт")
    return "\n".join(lines)


def format_broadcast_preview(
    text: str,
    recipient_count: int,
    *,
    filter: BroadcastFilter = BroadcastFilter.ALL,
) -> str:
    preview = escape(text[:400]) + ("…" if len(text) > 400 else "")
    cap = min(recipient_count, BROADCAST_MAX_RECIPIENTS)
    label = _FILTER_LABELS.get(filter.value, filter.value)
    return (
        "📢 <b>Превью рассылки</b>\n\n"
        f"{preview}\n\n"
        f"Аудитория: <b>{label}</b>\n"
        f"Получателей: <b>{cap}</b> из <b>{recipient_count}</b>.\n"
        "Фильтр можно сменить кнопками · «Себе» — проверка текста."
    )


def format_broadcast_body(text: str) -> str:
    return f"📢 <b>Сообщение от администратора</b>\n\n{escape(text)}"


async def send_broadcast_preview_to_admin(bot: Bot, admin_id: int, text: str) -> bool:
    try:
        await bot.send_message(admin_id, format_broadcast_body(text))
        return True
    except Exception as exc:
        logger.warning("Broadcast preview to admin %s failed: %s", admin_id, exc)
        return False


async def broadcast_message(
    bot: Bot,
    text: str,
    *,
    limit: int = BROADCAST_MAX_RECIPIENTS,
    filter: BroadcastFilter = BroadcastFilter.ALL,
) -> tuple[int, int, int]:
    """(delivered, failed, total_attempted)."""
    user_ids = await _select_broadcast_recipient_ids(filter, limit=limit)
    if not user_ids:
        return 0, 0, 0

    body = format_broadcast_body(text)
    delivered = 0
    failed = 0
    for tid in user_ids:
        try:
            await bot.send_message(tid, body)
            delivered += 1
        except Exception as exc:
            failed += 1
            logger.warning("Broadcast to %s failed: %s", tid, exc)
        if BROADCAST_DELAY_SEC:
            await asyncio.sleep(BROADCAST_DELAY_SEC)
    return delivered, failed, len(user_ids)


async def notify_other_admins(
    bot: Bot,
    sender_id: int,
    text: str,
    *,
    parse_mode: str = "HTML",
) -> None:
    for aid in settings.admin_telegram_ids:
        if aid == sender_id:
            continue
        try:
            await bot.send_message(aid, text, parse_mode=parse_mode)
        except Exception as exc:
            logger.warning("Notify admin %s failed: %s", aid, exc)
