"""Компактное inline-меню для групп — edit-in-place, без спама."""

from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    group_examples_keyboard,
    group_home_keyboard,
    group_timezone_keyboard,
)
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, tz_scope_label
from bot.services.callback_utils import safe_callback_answer
from bot.texts.messages import (
    format_group_create_hint,
    format_group_menu_home,
    format_help,
    format_group_private_only,
)

_last_menu_message: dict[int, int] = {}


def is_group_menu_chat(chat) -> bool:
    kind = chat_kind_from_chat(chat)
    return kind in (ChatKind.GROUP, ChatKind.SUPERGROUP)


def remember_group_menu_message(chat_id: int, message_id: int) -> None:
    _last_menu_message[chat_id] = message_id


def group_screen_content(screen: str, *, bot_username: str | None = None) -> tuple[str, object]:
    if screen == "hint":
        return format_group_create_hint(bot_username), group_home_keyboard()
    if screen == "help":
        return format_help(ChatKind.SUPERGROUP), group_home_keyboard()
    if screen == "tz":
        label = tz_scope_label(ChatKind.SUPERGROUP)
        return f"🕐 Часовой пояс ({label}):", group_timezone_keyboard()
    if screen == "examples":
        from bot.texts.messages import GROUP_EXAMPLES_INTRO

        return GROUP_EXAMPLES_INTRO, group_examples_keyboard()
    return format_group_menu_home(bot_username), group_home_keyboard()


async def _drop_previous_menu(bot: Bot, chat_id: int) -> None:
    message_id = _last_menu_message.pop(chat_id, None)
    if message_id is None:
        return
    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest:
        pass


async def _send_or_edit(
    target: Message,
    text: str,
    reply_markup,
    *,
    edit: bool,
) -> None:
    if edit:
        try:
            await target.edit_text(text, reply_markup=reply_markup)
            remember_group_menu_message(target.chat.id, target.message_id)
            return
        except TelegramBadRequest:
            pass
    sent = await target.answer(text, reply_markup=reply_markup)
    remember_group_menu_message(target.chat.id, sent.message_id)


async def show_group_menu_screen(
    callback: CallbackQuery,
    screen: str,
    bot: Bot,
    *,
    edit: bool = True,
) -> None:
    await safe_callback_answer(callback)
    me = await bot.get_me()
    text, kb = group_screen_content(screen, bot_username=me.username)
    await _send_or_edit(callback.message, text, kb, edit=edit)


async def send_group_menu_home(message: Message, bot: Bot) -> None:
    await send_group_menu_to_chat(bot, message.chat.id)


async def send_group_menu_to_chat(bot: Bot, chat_id: int) -> None:
    await _drop_previous_menu(bot, chat_id)
    me = await bot.get_me()
    text, kb = group_screen_content("home", bot_username=me.username)
    sent = await bot.send_message(chat_id, text, reply_markup=kb)
    remember_group_menu_message(chat_id, sent.message_id)


async def answer_group_private_only(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback, format_group_private_only(), show_alert=True)
