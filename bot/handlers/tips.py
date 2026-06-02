from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.stars_tips import (
    format_thanks_screen,
    format_tips_disabled,
    tip_keyboard,
    tips_enabled,
)

router = Router()


@router.message(Command("thanks", "support", "subscribe"))
async def cmd_thanks(message: Message) -> None:
    if not tips_enabled():
        await message.answer(
            format_tips_disabled(),
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return
    await message.answer(
        format_thanks_screen(),
        reply_markup=tip_keyboard(),
    )
