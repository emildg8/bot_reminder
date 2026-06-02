"""Проверка упоминания бота в collective-чатах (группа / канал)."""

from __future__ import annotations

import re

from aiogram.enums import ChatType
from aiogram.types import Message

from bot.services.chat_ctx import is_collective_chat
from bot.services.mention_parse import _is_bot_mention


def _contains_bot_mention_text(text: str, bot_username: str | None) -> bool:
    if not text or not bot_username:
        return False
    uname = re.escape(bot_username.lstrip("@"))
    pattern = re.compile(rf"(?<!\w)@{uname}(?=[^\w]|$)", re.IGNORECASE)
    return bool(pattern.search(text))


def _iter_message_entities(message: Message):
    for bucket in (message.entities, message.caption_entities):
        if bucket:
            yield from bucket


def is_reply_to_bot(message: Message, bot_id: int | None) -> bool:
    """Голос/текст ответом на сообщение бота — как @бот в группе."""
    if bot_id is None:
        return False
    reply = message.reply_to_message
    if reply is None or reply.from_user is None:
        return False
    return reply.from_user.id == bot_id


def is_bot_mentioned(
    message: Message,
    *,
    bot_username: str | None,
    bot_id: int | None,
) -> bool:
    text = message.text or message.caption or ""
    if text:
        for entity in _iter_message_entities(message):
            if entity.type == "mention":
                username = text[entity.offset + 1 : entity.offset + entity.length]
                if _is_bot_mention(username, bot_username, bot_id=bot_id):
                    return True
            if entity.type == "text_mention" and entity.user:
                if _is_bot_mention(
                    entity.user.username,
                    bot_username,
                    user_id=entity.user.id,
                    bot_id=bot_id,
                ):
                    return True
        if _contains_bot_mention_text(text, bot_username):
            return True

    return is_reply_to_bot(message, bot_id)


def _is_command_message(message: Message) -> bool:
    text = message.text or message.caption or ""
    return bool(text.strip().startswith("/"))


def should_handle_collective_message(
    message: Message,
    *,
    bot_username: str | None,
    bot_id: int | None,
) -> bool:
    """Личка — всегда. Группа — @бот. Канал — только команды (best practice)."""
    if not is_collective_chat(message.chat.id, message.chat.type):
        return True

    if message.chat.type == ChatType.CHANNEL:
        return _is_command_message(message)

    return is_bot_mentioned(message, bot_username=bot_username, bot_id=bot_id)


# Обратная совместимость
should_handle_group_text = should_handle_collective_message
