"""Справка с учётом режима админа."""

from __future__ import annotations

from aiogram.types import Chat, Message

from bot.services.admin_access import is_admin_listed, is_bot_admin
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat
from bot.texts.messages import format_admin_help_footer, format_help


def format_help_for_chat(chat: Chat, telegram_id: int) -> str:
    kind = chat_kind_from_chat(chat)
    text = format_help(kind)
    if kind == ChatKind.PRIVATE and is_admin_listed(telegram_id):
        text += "\n\n" + format_admin_help_footer(admin_tools=is_bot_admin(telegram_id))
    return text


def format_help_for_message(message: Message) -> str:
    return format_help_for_chat(message.chat, message.from_user.id)
