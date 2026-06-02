from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import about_developer_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_status import build_status_text
from bot.texts.messages import format_about
from bot.version import __version__

router = Router()


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(
        format_about(__version__),
        reply_markup=about_developer_keyboard(),
    )


@router.message(Command("status"))
async def cmd_status(message: Message, bot) -> None:
    text = await build_status_text(bot, message)
    await message.answer(text, reply_markup=menu_keyboard_for_chat(message.chat.id))
