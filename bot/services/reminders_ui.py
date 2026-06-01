from datetime import datetime

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from zoneinfo import ZoneInfo

from bot.config import settings
from bot.db.repository import (
    async_session,
    get_active_chat_reminders,
    get_history_events_for_day,
    get_inactive_chat_reminders,
    get_or_create_user,
    is_chat_paused,
)
from bot.keyboards.inline import list_page_keyboard, list_tabs_keyboard
from bot.services.chat_ctx import is_collective_chat
from bot.services.chat_delivery import resolve_delivery_chat_id
from bot.services.reminder_display import format_reminder_list_line
from bot.services.reminder_history import _day_bounds, _event_label

LIST_PAGE_SIZE = 8

COLLECTIVE_LIST_HINT = (
    "\n\n<i>✏️ /edit N · 🗑 /delete N (или /delete N yes)\n"
    "👤 — напоминание с тегом участника\n"
    "⏸ /pause · 🕐 /timezone (админы)\n"
    "Кнопки ✏️🗑 — только <b>свои</b> напоминания.</i>"
)

PRIVATE_LIST_HINT = (
    "\n\n<i>⏰ Отложить · ✅ Готово · ✏️ Изменить — кнопки под каждым напоминанием</i>"
)


def _paginate(items: list, page: int) -> tuple[list, int, int]:
    total_pages = max(1, (len(items) + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * LIST_PAGE_SIZE
    return items[start : start + LIST_PAGE_SIZE], page, total_pages


def _merge_keyboards(
    main: InlineKeyboardMarkup | None,
    tabs: InlineKeyboardMarkup | None,
) -> InlineKeyboardMarkup | None:
    rows = []
    if main:
        rows.extend(main.inline_keyboard)
    if tabs:
        rows.extend(tabs.inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def _collective_nav_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup | None:
    if total_pages <= 1:
        return None
    from aiogram.types import InlineKeyboardButton

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"list:page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="list:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"list:page:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[nav])


async def build_list_message(
    chat_id: int,
    viewer_id: int,
    page: int = 0,
    *,
    tab: str = "active",
    timezone: str = settings.default_timezone,
    source_chat_id: int | None = None,
) -> tuple[str, object | None]:
    ui_chat_id = source_chat_id if source_chat_id is not None else chat_id
    collective_ui = is_collective_chat(ui_chat_id)

    async with async_session() as session:
        paused = await is_chat_paused(session, chat_id)

        if tab == "history":
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            start, end = _day_bounds(now, tz)
            events = await get_history_events_for_day(
                session,
                chat_id,
                start=start,
                end=end,
                user_telegram_id=viewer_id,
                limit=100,
            )
            inactive = await get_inactive_chat_reminders(
                session, chat_id, limit=20, user_telegram_id=viewer_id
            )
            items = list(reversed(events))
            page_items, page, total_pages = _paginate(items, page)

            if not items and not inactive:
                body = (
                    "📜 <b>История за сегодня</b>\n\n"
                    "Пока пусто. Срабатывания, отложения и «Готово» сохраняются здесь."
                )
                return body, list_tabs_keyboard(active=False, page=page)

            lines = [f"📜 <b>История за сегодня</b> · {len(events)} событий"]
            if total_pages > 1:
                lines[0] += f" · стр. {page + 1}/{total_pages}"
            lines.append("")
            for event in page_items:
                lines.append(_event_label(event, tz))

            if inactive and page == 0:
                lines.append("")
                lines.append("<b>Закрытые напоминания</b>")
                for reminder in inactive[:5]:
                    lines.append(f"• {reminder.text} #{reminder.id}")

            tabs = list_tabs_keyboard(active=False, page=page)
            nav: list = []
            if page > 0:
                nav.append(("◀️", f"list:tab:history:{page - 1}"))
            if page < total_pages - 1:
                nav.append(("▶️", f"list:tab:history:{page + 1}"))
            if nav:
                from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

                nav_row = [InlineKeyboardButton(text=t, callback_data=d) for t, d in nav]
                merged = InlineKeyboardMarkup(inline_keyboard=[nav_row] + tabs.inline_keyboard)
                return "\n".join(lines), merged
            return "\n".join(lines), tabs

        reminders = await get_active_chat_reminders(session, chat_id)

    if not reminders:
        body = "📭 <b>Нет активных напоминаний</b>\n\nНапиши фразу или нажми ➕ Создать."
        return body, list_tabs_keyboard(active=True, page=page)

    page_items, page, total_pages = _paginate(reminders, page)
    lines = [format_reminder_list_line(r, r.timezone) for r in page_items]

    header = f"📋 <b>Активные</b> · {len(reminders)}"
    if chat_id != ui_chat_id:
        header += " · <i>канал</i>"
    if paused:
        header += " · ⏸ <i>на паузе</i>"
    if total_pages > 1:
        header += f" · стр. {page + 1}/{total_pages}"

    body = header + "\n\n" + "\n".join(lines)
    tabs = list_tabs_keyboard(active=True, page=page)

    if collective_ui:
        manage_kb = list_page_keyboard(page_items, viewer_id, page, total_pages)
        nav_kb = _collective_nav_keyboard(page, total_pages)
        merged = _merge_keyboards(manage_kb, nav_kb)
        merged = _merge_keyboards(merged, tabs)
        return body + COLLECTIVE_LIST_HINT, merged

    keyboard = list_page_keyboard(page_items, viewer_id, page, total_pages)
    return body + PRIVATE_LIST_HINT, _merge_keyboards(keyboard, tabs)


async def send_active_reminders(message: Message, page: int = 0, tab: str = "active") -> None:
    async with async_session() as session:
        await get_or_create_user(session, message.from_user.id, settings.default_timezone)
        list_chat_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )

    text, keyboard = await build_list_message(
        list_chat_id,
        message.from_user.id,
        page,
        tab=tab,
        source_chat_id=message.chat.id,
    )
    await message.answer(text, reply_markup=keyboard)


async def edit_list_message(callback: CallbackQuery, page: int, tab: str = "active") -> None:
    async with async_session() as session:
        list_chat_id = await resolve_delivery_chat_id(
            session, callback.message.chat.id, callback.message.chat.type
        )

    text, keyboard = await build_list_message(
        list_chat_id,
        callback.from_user.id,
        page,
        tab=tab,
        source_chat_id=callback.message.chat.id,
    )
    await callback.message.edit_text(text, reply_markup=keyboard)
