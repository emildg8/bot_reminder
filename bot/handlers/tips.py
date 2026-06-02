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


async def send_thanks_screen(
    message: Message,
    *,
    subscribe_redirect: bool = False,
) -> None:
    kb = menu_keyboard_for_chat(message.chat.id)
    if not tips_enabled():
        await message.answer(
            format_tips_disabled(from_subscribe=subscribe_redirect),
            reply_markup=kb,
        )
        return
    await message.answer(
        format_thanks_screen(subscribe_redirect=subscribe_redirect),
        reply_markup=tip_keyboard(),
    )


@router.message(Command("thanks", "support"))
async def cmd_thanks(message: Message) -> None:
    await send_thanks_screen(message)


@router.message(Command("subscribe"))
async def cmd_subscribe_redirect(message: Message) -> None:
    await send_thanks_screen(message, subscribe_redirect=True)
