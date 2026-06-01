"""Извлечение «кому» напоминание при создании/редактировании."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from bot.services.mention_parse import extract_leading_username, extract_mention_from_message


@dataclass(frozen=True)
class CreateMention:
    user_id: int | None
    username: str | None
    phrase: str
    source: str | None  # "text" | "reply" | None


def extract_reply_target(message: Message) -> tuple[int | None, str | None]:
    """Участник, на чьё сообщение ответили (reply)."""
    reply = message.reply_to_message
    if reply is None or reply.from_user is None:
        return None, None
    user = reply.from_user
    if user.is_bot:
        return None, None
    return user.id, user.username


def extract_create_mention(
    message: Message,
    phrase_text: str,
    *,
    bot_username: str | None,
    bot_id: int | None,
    from_transcription: bool = False,
) -> CreateMention:
    """
    Кому назначить напоминание.

    Приоритет: явный @ в тексте/entities → reply на сообщение участника.
    """
    phrase = phrase_text.strip()

    if from_transcription:
        username, clean = extract_leading_username(phrase, bot_username)
        if username:
            return CreateMention(None, username, clean, "text")
        reply_id, reply_uname = extract_reply_target(message)
        if reply_id:
            return CreateMention(reply_id, reply_uname, phrase, "reply")
        return CreateMention(None, None, phrase, None)

    mention_id, mention_username, clean = extract_mention_from_message(
        message,
        bot_username=bot_username,
        bot_id=bot_id,
    )
    if mention_username or mention_id:
        return CreateMention(mention_id, mention_username, clean or phrase, "text")

    reply_id, reply_uname = extract_reply_target(message)
    if reply_id:
        return CreateMention(reply_id, reply_uname, phrase, "reply")

    return CreateMention(None, None, phrase, None)


def mention_was_provided(mention: CreateMention) -> bool:
    return mention.source is not None
