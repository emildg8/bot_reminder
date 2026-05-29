import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.db.repository import async_session, search_chat_reminders
from bot.keyboards.reply import main_menu_keyboard
from bot.services.reminder_display import format_reminder_list_line

router = Router()

SEARCH_PATTERN = re.compile(r"^/search(?:@\w+)?(?:\s+(.+))?$", re.DOTALL | re.IGNORECASE)


@router.message(lambda m: m.text and SEARCH_PATTERN.match(m.text.strip()))
async def cmd_search(message: Message) -> None:
    match = SEARCH_PATTERN.match(message.text.strip())
    query = (match.group(1) or "").strip()

    if not query:
        await message.answer(
            "Формат: <code>/search таблетки</code>\n"
            "Ищет по тексту среди активных напоминаний в этом чате.",
            reply_markup=main_menu_keyboard(),
        )
        return

    async with async_session() as session:
        results = await search_chat_reminders(session, message.chat.id, query)

    if not results:
        await message.answer(f"По запросу «{query}» ничего не найдено.")
        return

    lines = [format_reminder_list_line(r, r.timezone) for r in results]
    await message.answer(
        f"🔍 Найдено: {len(results)}\n\n" + "\n".join(lines),
        reply_markup=main_menu_keyboard(),
    )
