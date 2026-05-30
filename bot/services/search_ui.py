"""Поиск напоминаний — общая логика для /search и кнопки меню."""

from __future__ import annotations

from aiogram.types import Message

from bot.db.repository import async_session, search_chat_reminders
from bot.keyboards.inline import list_page_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.reminder_display import format_reminder_list_line


async def send_search_results(message: Message, query: str) -> None:
    async with async_session() as session:
        results = await search_chat_reminders(session, message.chat.id, query)

    if not results:
        await message.answer(
            f"🔍 По запросу «{query}» ничего не найдено.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = [format_reminder_list_line(r, r.timezone) for r in results]
    keyboard = list_page_keyboard(results, message.from_user.id, 0, 1)
    await message.answer(
        f"🔍 Найдено: {len(results)}\n\n" + "\n".join(lines),
        reply_markup=keyboard or main_menu_keyboard(),
    )
