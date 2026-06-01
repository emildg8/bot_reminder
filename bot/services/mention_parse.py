import re

from aiogram.types import Message

USERNAME_PREFIX = re.compile(r"^@(\w{4,32})\s+", re.IGNORECASE)
TELEGRAM_COMMAND_PREFIX = re.compile(r"^/\w+(?:@\w+)?\s*", re.IGNORECASE)


def strip_telegram_command(text: str) -> str:
    return TELEGRAM_COMMAND_PREFIX.sub("", text.strip()).strip()


def command_prefix_length(text: str) -> int:
    match = TELEGRAM_COMMAND_PREFIX.match(text.strip())
    return match.end() if match else 0


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


def _remove_spans(text: str, spans: list[tuple[int, int]]) -> str:
    if not spans:
        return text.strip()
    parts: list[str] = []
    pos = 0
    for start, length in sorted(spans):
        if start < pos:
            continue
        parts.append(text[pos:start])
        pos = start + length
    parts.append(text[pos:])
    return "".join(parts).strip()


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
    raw = (message.text or message.caption or "").strip()
    if not raw:
        return None, None, raw

    prefix_len = command_prefix_length(raw)
    text = raw[prefix_len:].strip()

    clean = text
    mention_id: int | None = None
    mention_username: str | None = None
    removed_spans: list[tuple[int, int]] = []

    if message.entities:
        for entity in message.entities:
            if entity.offset + entity.length <= prefix_len:
                continue

            rel_start = max(0, entity.offset - prefix_len)

            if entity.type == "text_mention" and entity.user:
                if entity.user.is_bot or _is_bot_mention(
                    entity.user.username,
                    bot_username,
                    user_id=entity.user.id,
                    bot_id=bot_id,
                ):
                    removed_spans.append((rel_start, entity.length))
                    continue
                mention_id = entity.user.id
                mention_username = entity.user.username
                removed_spans.append((rel_start, entity.length))
                break

            if entity.type == "mention":
                username = raw[entity.offset + 1 : entity.offset + entity.length]
                if _is_bot_mention(username, bot_username):
                    removed_spans.append((rel_start, entity.length))
                    continue
                mention_id = None
                mention_username = username
                removed_spans.append((rel_start, entity.length))
                break

        if removed_spans:
            clean = _remove_spans(text, removed_spans)

    if mention_username is None and mention_id is None:
        username, clean = extract_leading_username(clean, bot_username)
        if username:
            mention_username = username

    return mention_id, mention_username, clean or text
