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
from bot.services.reminder_display import format_reminder_list_line
from bot.services.reminder_history import _day_bounds, _event_label

LIST_PAGE_SIZE = 8


def _paginate(items: list, page: int) -> tuple[list, int, int]:
    total_pages = max(1, (len(items) + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * LIST_PAGE_SIZE
    return items[start : start + LIST_PAGE_SIZE], page, total_pages


def _merge_keyboards(
    main: InlineKeyboardMarkup | None,
    tabs: InlineKeyboardMarkup,
) -> InlineKeyboardMarkup | None:
    rows = []
    if main:
        rows.extend(main.inline_keyboard)
    rows.extend(tabs.inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def build_list_message(
    chat_id: int,
    viewer_id: int,
    page: int = 0,
    *,
    tab: str = "active",
    timezone: str = settings.default_timezone,
) -> tuple[str, object | None]:
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
    if paused:
        header += " · ⏸ <i>на паузе</i>"
    if total_pages > 1:
        header += f" · стр. {page + 1}/{total_pages}"

    body = header + "\n\n" + "\n".join(lines)
    hint = ""
    if chat_id < 0:
        hint = "\n\n<i>Кнопки ✏️/🗑 — только для своих.</i>"

    keyboard = list_page_keyboard(page_items, viewer_id, page, total_pages)
    tabs = list_tabs_keyboard(active=True, page=page)
    return body + hint, _merge_keyboards(keyboard, tabs)


async def send_active_reminders(message: Message, page: int = 0, tab: str = "active") -> None:
    async with async_session() as session:
        await get_or_create_user(session, message.from_user.id, settings.default_timezone)

    text, keyboard = await build_list_message(message.chat.id, message.from_user.id, page, tab=tab)
    await message.answer(text, reply_markup=keyboard)


async def edit_list_message(callback: CallbackQuery, page: int, tab: str = "active") -> None:
    text, keyboard = await build_list_message(
        callback.message.chat.id, callback.from_user.id, page, tab=tab
    )
    await callback.message.edit_text(text, reply_markup=keyboard)
