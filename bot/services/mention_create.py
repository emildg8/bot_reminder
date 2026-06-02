"""Извлечение «кому» напоминание при создании/редактировании."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from bot.services.mention_parse import (
    assignee_pick_for_count,
    extract_leading_username,
    extract_mention_from_message,
    extract_username_anywhere,
    extract_username_candidates,
    format_assignee_pick_note,
    strip_leading_bot_mention,
)


@dataclass(frozen=True)
class CreateMention:
    user_id: int | None
    username: str | None
    phrase: str
    source: str | None  # "text" | "reply" | None
    pick_note: str | None = None


def _enrich_pick_context(
    message: Message,
    mention: CreateMention,
    *,
    bot_username: str | None,
) -> CreateMention:
    if mention.source != "text" or not mention.username:
        return mention
    raw = (message.text or message.caption or "").strip()
    candidates, _ = extract_username_candidates(raw, bot_username)
    if len(candidates) <= 1:
        return mention
    note = format_assignee_pick_note(
        raw,
        chosen=mention.username,
        candidates=candidates,
    )
    return CreateMention(
        mention.user_id,
        mention.username,
        mention.phrase,
        mention.source,
        pick_note=note,
    )


def extract_reply_target(message: Message) -> tuple[int | None, str | None]:
    """Участник, на чьё сообщение ответили (reply)."""
    reply = message.reply_to_message
    if reply is None or reply.from_user is None:
        return None, None
    user = reply.from_user
    if getattr(user, "is_bot", False):
        return None, None
    user_id = getattr(user, "id", None)
    if not isinstance(user_id, int):
        return None, None
    username = getattr(user, "username", None)
    if username is not None and not isinstance(username, str):
        username = None
    return user_id, username


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
        stripped = strip_leading_bot_mention(phrase, bot_username)
        username, clean = extract_leading_username(stripped, bot_username)
        if not username:
            candidates, _ = extract_username_candidates(stripped, bot_username)
            pick = assignee_pick_for_count(len(candidates))
            username, clean = extract_username_anywhere(stripped, bot_username, pick=pick)
        if username:
            base = CreateMention(None, username, clean, "text")
            return _enrich_pick_context(message, base, bot_username=bot_username)
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
        base = CreateMention(mention_id, mention_username, clean or phrase, "text")
        return _enrich_pick_context(message, base, bot_username=bot_username)

    reply_id, reply_uname = extract_reply_target(message)
    if reply_id:
        return CreateMention(reply_id, reply_uname, phrase, "reply")

    return CreateMention(None, None, phrase, None)


def mention_was_provided(mention: CreateMention) -> bool:
    return mention.source is not None
