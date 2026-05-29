from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_active_chat_reminders, get_or_create_user, is_chat_paused
from bot.keyboards.inline import list_page_keyboard
from bot.services.reminder_display import format_reminder_list_line

LIST_PAGE_SIZE = 8


def _paginate(items: list, page: int) -> tuple[list, int, int]:
    total_pages = max(1, (len(items) + LIST_PAGE_SIZE - 1) // LIST_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    start = page * LIST_PAGE_SIZE
    return items[start : start + LIST_PAGE_SIZE], page, total_pages


async def build_list_message(chat_id: int, viewer_id: int, page: int = 0) -> tuple[str, object | None]:
    async with async_session() as session:
        paused = await is_chat_paused(session, chat_id)
        reminders = await get_active_chat_reminders(session, chat_id)

    if not reminders:
        return "📭 <b>Нет активных напоминаний</b>\n\nНапиши фразу или нажми ➕ Создать.", None

    page_items, page, total_pages = _paginate(reminders, page)
    lines = [format_reminder_list_line(r, r.timezone) for r in page_items]

    header = f"📋 <b>Напоминания</b> · {len(reminders)}"
    if paused:
        header += " · ⏸ <i>на паузе</i>"
    if total_pages > 1:
        header += f" · стр. {page + 1}/{total_pages}"

    body = header + "\n\n" + "\n".join(lines)
    hint = ""
    if chat_id < 0:
        hint = "\n\n<i>Кнопки ✏️/🗑 — только для своих.</i>"

    keyboard = list_page_keyboard(page_items, viewer_id, page, total_pages)
    return body + hint, keyboard


async def send_active_reminders(message: Message, page: int = 0) -> None:
    async with async_session() as session:
        await get_or_create_user(session, message.from_user.id, settings.default_timezone)

    text, keyboard = await build_list_message(message.chat.id, message.from_user.id, page)
    await message.answer(text, reply_markup=keyboard)


async def edit_list_message(callback: CallbackQuery, page: int) -> None:
    text, keyboard = await build_list_message(callback.message.chat.id, callback.from_user.id, page)
    await callback.message.edit_text(text, reply_markup=keyboard)
