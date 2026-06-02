import re
from typing import Literal

from aiogram.types import Message

_MENTION_SEP_CHARS = r"[\s+,:;\-–—|/\\.\(\)\[\]{}«»]"
USERNAME_PREFIX = re.compile(
    rf"^(?:{_MENTION_SEP_CHARS}+)?@(\w{{4,32}})(?:{_MENTION_SEP_CHARS}+)",
    re.IGNORECASE,
)
TELEGRAM_COMMAND_PREFIX = re.compile(r"^/\w+(?:@\w+)?\s*", re.IGNORECASE)
LEADING_MENTION_SEPARATORS = re.compile(rf"^{_MENTION_SEP_CHARS}+")
USERNAME_ANYWHERE = re.compile(
    r"@(\w{4,32})(?=[^\w]|$)",
    re.IGNORECASE,
)
_COLLAPSE_WS = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.:;!?%])")
MentionPick = Literal["first", "last"]


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


def strip_leading_bot_mention(text: str, bot_username: str | None) -> str:
    """Убирает ведущий @бот в group-тексте: '@bot ...' / '@bot@user ...'."""
    raw = (text or "").strip()
    if not raw or not bot_username:
        return raw
    token = f"@{_normalize_username(bot_username)}"
    lowered = raw.lower()
    if not lowered.startswith(token):
        return raw
    tail = LEADING_MENTION_SEPARATORS.sub("", raw[len(token) :])
    return tail.strip()


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


def _user_mention_spans(
    text: str,
    bot_username: str | None,
) -> list[tuple[int, int, str]]:
    """(start, end, username) для каждого @user, кроме бота, слева направо."""
    raw = (text or "").strip()
    if not raw:
        return []
    spans: list[tuple[int, int, str]] = []
    for match in USERNAME_ANYWHERE.finditer(raw):
        username = match.group(1)
        if _is_bot_mention(username, bot_username):
            continue
        spans.append((match.start(), match.end(), username))
    return spans


def _normalize_phrase_whitespace(text: str) -> str:
    compact = _COLLAPSE_WS.sub(" ", (text or "").strip())
    return _SPACE_BEFORE_PUNCT.sub(r"\1", compact)


def _pick_username(spans: list[tuple[int, int, str]], pick: MentionPick) -> str | None:
    if not spans:
        return None
    if pick == "last":
        return spans[-1][2]
    return spans[0][2]


def extract_username_candidates(
    text: str,
    bot_username: str | None = None,
) -> tuple[list[str], str]:
    """
    Возвращает всех найденных @user (не бот) в порядке слева-направо + clean без @user.
    Нужен для A/B-логики выбора assignee на уровне вызывающего кода.
    """
    raw = strip_leading_bot_mention((text or "").strip(), bot_username)
    spans = _user_mention_spans(raw, bot_username)
    usernames = [username for _, _, username in spans]
    clean = strip_all_user_mentions(raw, bot_username) if spans else raw
    return usernames, clean


def strip_all_bot_mentions(text: str, bot_username: str | None = None) -> str:
    """Убирает все @бот из текста (не только в начале)."""
    raw = (text or "").strip()
    if not raw or not bot_username:
        return raw
    remove = [
        (match.start(), match.end() - match.start())
        for match in USERNAME_ANYWHERE.finditer(raw)
        if _is_bot_mention(match.group(1), bot_username)
    ]
    if not remove:
        return raw
    clean = _remove_spans(raw, remove)
    return LEADING_MENTION_SEPARATORS.sub("", clean.strip()).strip()


def strip_all_user_mentions(text: str, bot_username: str | None = None) -> str:
    """Убирает все @user (не бот) из текста, assignee не меняет."""
    raw = (text or "").strip()
    spans = _user_mention_spans(raw, bot_username)
    if not spans:
        return _normalize_phrase_whitespace(raw)
    remove = [(start, end - start) for start, end, _ in spans]
    clean = _remove_spans(raw, remove)
    clean = LEADING_MENTION_SEPARATORS.sub("", clean.strip()).strip()
    return _normalize_phrase_whitespace(clean)


def extract_leading_username(text: str, bot_username: str | None = None) -> tuple[str | None, str]:
    match = USERNAME_PREFIX.match(text.strip())
    if not match:
        return None, text.strip()
    username = match.group(1)
    if _is_bot_mention(username, bot_username):
        return None, text[match.end() :].strip()
    clean = text[match.end() :].strip()
    return username, strip_all_user_mentions(clean, bot_username)


def extract_username_anywhere(
    text: str,
    bot_username: str | None = None,
    *,
    pick: MentionPick = "first",
) -> tuple[str | None, str]:
    """
    Выбор assignee из текста по варианту:
    - first (default): первый @user слева
    - last: последний @user
    """
    usernames, clean = extract_username_candidates(text, bot_username)
    if not usernames:
        return None, clean
    return (usernames[-1] if pick == "last" else usernames[0]), clean


def extract_mention_from_message(
    message: Message,
    *,
    bot_username: str | None = None,
    bot_id: int | None = None,
) -> tuple[int | None, str | None, str]:
    """Возвращает (telegram_user_id, username, очищенный текст). Упоминание бота пропускается."""
    raw = message.text or message.caption or ""
    if not isinstance(raw, str):
        raw = ""
    raw = raw.strip()
    if not raw:
        return None, None, raw

    prefix_len = command_prefix_length(raw)
    text = raw[prefix_len:].strip()

    clean = text
    mention_id: int | None = None
    mention_username: str | None = None
    removed_spans: list[tuple[int, int]] = []

    if message.entities:
        for entity in sorted(message.entities, key=lambda e: e.offset):
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
                if mention_id is None and mention_username is None:
                    mention_id = entity.user.id
                    mention_username = entity.user.username
                removed_spans.append((rel_start, entity.length))
                continue

            if entity.type == "mention":
                username = raw[entity.offset + 1 : entity.offset + entity.length]
                if _is_bot_mention(username, bot_username):
                    removed_spans.append((rel_start, entity.length))
                    continue
                if mention_id is None and mention_username is None:
                    mention_id = None
                    mention_username = username
                removed_spans.append((rel_start, entity.length))
                continue

        if removed_spans:
            clean = _remove_spans(text, removed_spans)
            clean = strip_all_user_mentions(clean, bot_username)

    if mention_username is None and mention_id is None:
        clean = strip_leading_bot_mention(clean, bot_username)
        username, clean = extract_leading_username(clean, bot_username)
        if username:
            mention_username = username
        else:
            username, clean = extract_username_anywhere(clean, bot_username)
            if username:
                mention_username = username

    clean = strip_all_bot_mentions(clean or text, bot_username)
    clean = _normalize_phrase_whitespace(clean)
    return mention_id, mention_username, clean
