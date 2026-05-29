from aiogram import Router
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from bot.keyboards.inline import main_menu_inline_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.texts.messages import GROUP_WELCOME

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_bot_added(event: ChatMemberUpdated) -> None:
    if event.chat.type not in ("group", "supergroup"):
        return

    await event.bot.send_message(
        event.chat.id,
        GROUP_WELCOME,
        reply_markup=main_menu_keyboard(),
    )
    await event.bot.send_message(
        event.chat.id,
        "⚡️ Быстрые действия:",
        reply_markup=main_menu_inline_keyboard(),
    )
