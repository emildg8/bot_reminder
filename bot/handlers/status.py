from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.repository import async_session, get_active_chat_reminders, is_chat_paused
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, tz_scope_label
from bot.services.timezone_ctx import get_effective_timezone, is_group_chat
from bot.texts.messages import format_about, format_help, format_status
from bot.version import __version__

router = Router()


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(format_about(__version__), reply_markup=menu_keyboard_for_chat(message.chat.id))


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    chat_id = message.chat.id
    async with async_session() as session:
        count = len(await get_active_chat_reminders(session, chat_id))
        paused = await is_chat_paused(session, chat_id)
        tz = await get_effective_timezone(session, chat_id, message.from_user.id)

    kind = chat_kind_from_chat(message.chat)
    await message.answer(
        format_status(
            count=count,
            paused=paused,
            tz=tz,
            tz_scope=tz_scope_label(kind),
            version=__version__,
            chat_kind=kind,
        ),
        reply_markup=menu_keyboard_for_chat(chat_id),
    )
