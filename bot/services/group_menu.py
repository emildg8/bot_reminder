"""Группы — без inline-меню, только команды и текст."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from bot.services.callback_utils import safe_callback_answer
from bot.texts.messages import format_group_commands_hint, format_group_private_only


def is_group_menu_chat(chat) -> bool:
    from bot.services.chat_ctx import ChatKind, chat_kind_from_chat

    kind = chat_kind_from_chat(chat)
    return kind in (ChatKind.GROUP, ChatKind.SUPERGROUP)


async def send_group_commands_to_chat(bot: Bot, chat_id: int) -> None:
    me = await bot.get_me()
    await bot.send_message(chat_id, format_group_commands_hint(me.username))


async def send_group_commands_hint(message: Message, bot: Bot) -> None:
    await send_group_commands_to_chat(bot, message.chat.id)


async def dismiss_legacy_group_menu(callback: CallbackQuery) -> None:
    """Старые inline-меню в группе — убрать клавиатуру, подсказать команды."""
    await safe_callback_answer(
        callback,
        "В группе используй команды: /remind /list /help",
        show_alert=True,
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


async def answer_group_private_only(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback, format_group_private_only(), show_alert=True)
