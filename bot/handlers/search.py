import re

from aiogram import Router
from aiogram.types import Message

from bot.keyboards.reply import main_menu_keyboard
from bot.services.search_ui import send_search_results

router = Router()

SEARCH_PATTERN = re.compile(r"^/search(?:@\w+)?(?:\s+(.+))?$", re.DOTALL | re.IGNORECASE)


@router.message(lambda m: m.text and SEARCH_PATTERN.match(m.text.strip()))
async def cmd_search(message: Message) -> None:
    match = SEARCH_PATTERN.match(message.text.strip())
    query = (match.group(1) or "").strip()

    if not query:
        await message.answer(
            "Формат: <code>/search таблетки</code>\n"
            "Или нажми 🔍 Поиск в меню и напиши слово.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await send_search_results(message, query)
