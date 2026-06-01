from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_status import build_status_text
from bot.services.subscription import format_monetization_disabled, monetization_active

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


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    from bot.db.repository import async_session, count_active_reminders_for_user
    from bot.handlers.payments import send_subscribe_with_payment

    if not monetization_active():
        await message.answer(
            format_monetization_disabled(),
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    async with async_session() as session:
        current = await count_active_reminders_for_user(session, message.from_user.id)

    await send_subscribe_with_payment(message, current=current)
