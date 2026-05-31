from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from bot.keyboards.inline import main_menu_inline_keyboard
from bot.services.bot_menu import setup_channel_commands
from bot.services.chat_ctx import ChatKind, chat_kind_from_type
from bot.texts.messages import format_collective_welcome

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_bot_added(event: ChatMemberUpdated) -> None:
    chat_type = event.chat.type
    if chat_type not in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
        return

    kind = chat_kind_from_type(chat_type)
    me = await event.bot.get_me()
    welcome = format_collective_welcome(kind, me.username)

    await event.bot.send_message(event.chat.id, welcome)

    if kind == ChatKind.CHANNEL:
        await setup_channel_commands(event.bot, event.chat.id)
    else:
        await event.bot.send_message(
            event.chat.id,
            "⚡️ Быстрые действия:",
            reply_markup=main_menu_inline_keyboard(),
        )
