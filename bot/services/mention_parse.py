import re

from aiogram.types import Message

USERNAME_PREFIX = re.compile(r"^@(\w{4,32})\s+", re.IGNORECASE)


def _normalize_username(username: str | None) -> str | None:
    if not username:
        return None
    return username.lstrip("@").lower()


def _is_bot_mention(
    username: str | None,
    bot_username: str | None,
    *,
    user_id: int | None = None,
    bot_id: int | None = None,
) -> bool:
    if bot_id is not None and user_id is not None and user_id == bot_id:
        return True
    if username and bot_username:
        return _normalize_username(username) == _normalize_username(bot_username)
    return False


def extract_leading_username(text: str, bot_username: str | None = None) -> tuple[str | None, str]:
    match = USERNAME_PREFIX.match(text.strip())
    if not match:
        return None, text.strip()
    username = match.group(1)
    if _is_bot_mention(username, bot_username):
        return None, text[match.end() :].strip()
    return username, text[match.end() :].strip()


def extract_mention_from_message(
    message: Message,
    *,
    bot_username: str | None = None,
    bot_id: int | None = None,
) -> tuple[int | None, str | None, str]:
    """Возвращает (telegram_user_id, username, очищенный текст). Упоминание бота пропускается."""
    text = (message.text or message.caption or "").strip()
    if not text:
        return None, None, text

    clean = text
    mention_id: int | None = None
    mention_username: str | None = None

    if message.entities:
        skip_spans: list[tuple[int, int]] = []
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                if entity.user.is_bot or _is_bot_mention(
                    entity.user.username,
                    bot_username,
                    user_id=entity.user.id,
                    bot_id=bot_id,
                ):
                    skip_spans.append((entity.offset, entity.length))
                    continue
                mention_id = entity.user.id
                mention_username = entity.user.username
                clean = (text[: entity.offset] + text[entity.offset + entity.length :]).strip()
                break
            if entity.type == "mention":
                username = text[entity.offset + 1 : entity.offset + entity.length]
                if _is_bot_mention(username, bot_username):
                    skip_spans.append((entity.offset, entity.length))
                    continue
                mention_id = None
                mention_username = username
                clean = (text[: entity.offset] + text[entity.offset + entity.length :]).strip()
                break

        if skip_spans and mention_username is None:
            parts: list[str] = []
            pos = 0
            for start, length in sorted(skip_spans):
                parts.append(text[pos:start])
                pos = start + length
            parts.append(text[pos:])
            clean = "".join(parts).strip()

    if mention_username is None and mention_id is None:
        username, clean = extract_leading_username(clean, bot_username)
        if username:
            mention_username = username

    return mention_id, mention_username, clean or text
