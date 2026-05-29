from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.repository import async_session, get_active_chat_reminders, is_chat_paused
from bot.keyboards.reply import main_menu_keyboard
from bot.services.timezone_ctx import get_effective_timezone, is_group_chat
from bot.texts.messages import format_status
from bot.version import __version__

router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    chat_id = message.chat.id
    async with async_session() as session:
        count = len(await get_active_chat_reminders(session, chat_id))
        paused = await is_chat_paused(session, chat_id)
        tz = await get_effective_timezone(session, chat_id, message.from_user.id)

    tz_scope = "группы" if is_group_chat(chat_id) else "твой"
    await message.answer(
        format_status(count=count, paused=paused, tz=tz, tz_scope=tz_scope, version=__version__),
        reply_markup=main_menu_keyboard(),
    )
