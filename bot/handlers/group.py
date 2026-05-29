from aiogram import Router
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from bot.keyboards.inline import main_menu_inline_keyboard
from bot.keyboards.reply import main_menu_keyboard

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_bot_added(event: ChatMemberUpdated) -> None:
    if event.chat.type not in ("group", "supergroup"):
        return

    await event.bot.send_message(
        event.chat.id,
        "Привет! Я напоминалка для этой группы.\n\n"
        "Напиши фразу, например:\n"
        "• через 30 минут созвон\n"
        "• по будням в 09:00 стендап\n\n"
        "Часовой пояс группы: /timezone\n"
        "Команды: /list /search /pause /help /menu",
        reply_markup=main_menu_keyboard(),
    )
    await event.bot.send_message(
        event.chat.id,
        "Быстрые действия:",
        reply_markup=main_menu_inline_keyboard(),
    )
