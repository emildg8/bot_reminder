from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from bot.config import settings
from bot.db.repository import async_session, find_channel_by_linked_chat, get_or_create_chat
from bot.keyboards.inline import timezone_keyboard
from bot.services.bot_menu import setup_channel_commands
from bot.services.chat_ctx import ChatKind, chat_kind_from_type
from bot.services.chat_delivery import resolve_delivery_chat_id, sync_channel_linked_chat
from bot.texts.messages import (
    format_collective_welcome,
    format_discussion_channel_hint,
    format_group_tz_onboarding,
)

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
        async with async_session() as session:
            await sync_channel_linked_chat(
                event.bot,
                session,
                event.chat.id,
                default_timezone=settings.default_timezone,
            )
    else:
        async with async_session() as session:
            ops_id = await resolve_delivery_chat_id(
                session, event.chat.id, chat_type
            )
            chat = await get_or_create_chat(session, ops_id, settings.default_timezone)
            if not chat.timezone_confirmed:
                await event.bot.send_message(
                    event.chat.id,
                    format_group_tz_onboarding(),
                    reply_markup=timezone_keyboard(),
                )
            linked_channel_id = None
            try:
                full = await event.bot.get_chat(event.chat.id)
                linked_channel_id = getattr(full, "linked_chat_id", None)
            except Exception:
                pass
            if linked_channel_id and ops_id == event.chat.id:
                parent = await find_channel_by_linked_chat(session, event.chat.id)
                if parent is None:
                    await event.bot.send_message(
                        event.chat.id,
                        format_discussion_channel_hint(me.username),
                    )

