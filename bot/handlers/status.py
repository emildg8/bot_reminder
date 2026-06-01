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


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    from bot.db.repository import async_session, count_active_reminders_for_user
    from bot.services.subscription import format_subscribe_message, is_pro_user
    from bot.config import settings

    async with async_session() as session:
        from bot.db.repository import get_user_by_telegram_id

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if is_pro_user(user, message.from_user.id):
            await message.answer(
                "⭐ У тебя уже <b>Pro</b> — лимит активных напоминаний снят.",
                reply_markup=menu_keyboard_for_chat(message.chat.id),
            )
            return
        current = await count_active_reminders_for_user(session, message.from_user.id)

    await message.answer(
        format_subscribe_message(current=current, limit=settings.free_active_limit),
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )
