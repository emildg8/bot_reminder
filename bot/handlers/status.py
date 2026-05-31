from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.repository import async_session, get_active_chat_reminders, is_chat_paused
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, is_collective_chat, tz_scope_label
from bot.services.chat_delivery import resolve_delivery_chat_id
from bot.services.chat_permissions import bot_can_post_reminders
from bot.services.status_info import format_next_reminder_line
from bot.services.timezone_ctx import get_effective_timezone
from bot.texts.messages import format_about, format_help, format_status
from bot.version import __version__

router = Router()


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(format_about(__version__), reply_markup=menu_keyboard_for_chat(message.chat.id))


@router.message(Command("status"))
async def cmd_status(message: Message, bot: Bot) -> None:
    kind = chat_kind_from_chat(message.chat)
    async with async_session() as session:
        delivery_id = await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )
        reminders = await get_active_chat_reminders(session, delivery_id)
        count = len(reminders)
        paused = await is_chat_paused(session, delivery_id)
        tz = await get_effective_timezone(session, delivery_id, message.from_user.id)

    next_line = format_next_reminder_line(reminders, tz)
    delivery_line = None
    if delivery_id != message.chat.id:
        delivery_line = "📢 Доставка: <b>в связанный канал</b>"

    post_ok = None
    if is_collective_chat(message.chat.id):
        post_ok = await bot_can_post_reminders(bot, delivery_id)

    await message.answer(
        format_status(
            count=count,
            paused=paused,
            tz=tz,
            tz_scope=tz_scope_label(kind),
            version=__version__,
            chat_kind=kind,
            next_line=next_line,
            delivery_line=delivery_line,
            post_ok=post_ok,
        ),
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )
