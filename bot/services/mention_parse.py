import re

from aiogram.types import Message

USERNAME_PREFIX = re.compile(r"^@(\w{4,32})\s+", re.IGNORECASE)


def extract_leading_username(text: str) -> tuple[str | None, str]:
    match = USERNAME_PREFIX.match(text.strip())
    if not match:
        return None, text.strip()
    return match.group(1), text[match.end() :].strip()


def extract_mention_from_message(message: Message) -> tuple[int | None, str | None, str]:
    """Возвращает (telegram_user_id, username, очищенный текст)."""
    text = (message.text or message.caption or "").strip()
    if not text:
        return None, None, text

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                clean = (text[: entity.offset] + text[entity.offset + entity.length :]).strip()
                return entity.user.id, entity.user.username, clean or text
            if entity.type == "mention":
                username = text[entity.offset + 1 : entity.offset + entity.length]
                clean = (text[: entity.offset] + text[entity.offset + entity.length :]).strip()
                return None, username, clean or text

    username, clean = extract_leading_username(text)
    return None, username, clean
