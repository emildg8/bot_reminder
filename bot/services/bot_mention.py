"""Проверка упоминания бота в сообщении группы."""

from __future__ import annotations

from aiogram.types import Message

from bot.services.mention_parse import _is_bot_mention
from bot.services.timezone_ctx import is_group_chat


def is_bot_mentioned(
    message: Message,
    *,
    bot_username: str | None,
    bot_id: int | None,
) -> bool:
    text = message.text or message.caption or ""
    if not text:
        return False

    if message.entities:
        for entity in message.entities:
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

    if bot_username:
        token = f"@{bot_username}".lower()
        if token in text.lower():
            return True
    return False


def should_handle_group_text(
    message: Message,
    *,
    bot_username: str | None,
    bot_id: int | None,
) -> bool:
    if not is_group_chat(message.chat.id):
        return True
    return is_bot_mentioned(message, bot_username=bot_username, bot_id=bot_id)
