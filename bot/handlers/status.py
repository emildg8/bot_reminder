from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_status import build_status_text

router = Router()


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    from bot.texts.messages import format_about
    from bot.version import __version__

    await message.answer(format_about(__version__), reply_markup=menu_keyboard_for_chat(message.chat.id))


@router.message(Command("status"))
async def cmd_status(message: Message, bot: Bot) -> None:
    text = await build_status_text(bot, message)
    await message.answer(text, reply_markup=menu_keyboard_for_chat(message.chat.id))
