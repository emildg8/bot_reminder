import re
from typing import Literal

from aiogram.types import Message, MessageEntity

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
_EMPTY_BRACKETS = re.compile(r"\s*(\(\s*\)|\[\s*\]|\{\s*\})\s*")
_TIME_ANCHOR_RE = re.compile(
    r"(?:"
    r"\bчерез\b|"
    r"завтра|сегодня|послезавтра|после\s+завтра|"
    r"кажд|утром|вечером|ночью|днём|днем|"
    r"понедельник|вторник|сред[ау]|четверг|пятниц[ау]|суббот[ау]|воскресень[ея]|"
    r"в\s*\d{1,2}(?:[.:]\d{2})?|"
    r"в\s+\d{3,4}\b"
    r")",
    re.IGNORECASE,
)
FOR_USER_PREFIX = re.compile(
    rf"^(?:для|кому|напомни(?:ть)?|напоминание\s+для)\s*(?:{_MENTION_SEP_CHARS}+)?"
    rf"@(\w{{4,32}})(?:{_MENTION_SEP_CHARS}+)",
    re.IGNORECASE,
)
MentionPick = Literal["first", "last", "nearest_time", "auto"]
_PLAIN_NAME = re.compile(
    r"^([A-Za-zА-Яа-яЁё][\w''\-]*(?:\s+[A-Za-zА-Яа-яЁё][\w''\-]*){0,2})$"
)


def _utf16_units(char: str) -> int:
    return 2 if ord(char) > 0xFFFF else 1


def utf16_offset_to_index(text: str, utf16_offset: int) -> int:
    """Telegram entity offset (UTF-16) → индекс символа Python."""
    if utf16_offset <= 0:
        return 0
    units = 0
    for index, char in enumerate(text):
        if units >= utf16_offset:
            return index
        units += _utf16_units(char)
    return len(text)


def _entity_span_py(raw: str, entity: MessageEntity) -> tuple[int, int]:
    start = utf16_offset_to_index(raw, entity.offset)
    end = utf16_offset_to_index(raw, entity.offset + entity.length)
    return start, end


def _phrase_window(raw: str) -> tuple[str, int]:
    """Текст фразы и его начало (Python index) в raw."""
    prefix_py = command_prefix_length(raw)
    tail = raw[prefix_py:]
    phrase_start_py = prefix_py + (len(tail) - len(tail.lstrip()))
    return tail.lstrip(), phrase_start_py


def _message_text_and_entities(message: Message) -> tuple[str, list[MessageEntity]]:
    """Текст сообщения и entities (text или caption)."""
    raw = message.text or message.caption or ""
    if not isinstance(raw, str):
        raw = ""
    raw = raw.strip()
    if message.text:
        entities = list(message.entities or [])
    else:
        entities = list(message.caption_entities or [])
    return raw, entities


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


def strip_text_before_bot_mention(text: str, bot_username: str | None) -> str:
    """Обрезает всё до первого @бот (включая его), если он есть в сообщении."""
    raw = (text or "").strip()
    if not raw or not bot_username:
        return raw
    lowered = raw.lower()
    token = f"@{_normalize_username(bot_username)}"
    idx = lowered.find(token)
    if idx < 0:
        return raw
    tail = raw[idx + len(token) :]
    tail = LEADING_MENTION_SEPARATORS.sub("", tail)
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
    no_empty_brackets = _EMPTY_BRACKETS.sub(" ", (text or "").strip())
    compact = _COLLAPSE_WS.sub(" ", no_empty_brackets)
    return _SPACE_BEFORE_PUNCT.sub(r"\1", compact).strip()


def _time_anchor_index(text: str) -> int | None:
    match = _TIME_ANCHOR_RE.search(text or "")
    return match.start() if match else None


def _extract_leading_plain_name(text: str) -> tuple[str | None, str]:
    """
    Имя без @ из списка Telegram (text_mention) или набранное вручную после @бот.
    Берём только фрагмент до якоря времени («через», «завтра», «в 10:00» …).
    """
    raw = (text or "").strip()
    if not raw:
        return None, raw
    first_token = raw.split(maxsplit=1)[0]
    if first_token.startswith("@"):
        return None, raw
    anchor = _time_anchor_index(raw)
    head = raw if anchor is None else raw[:anchor]
    head = head.strip()
    if not head or "@" in head:
        return None, raw
    match = _PLAIN_NAME.match(head)
    if not match:
        return None, raw
    name = match.group(1).strip()
    if len(name) < 2 or _TIME_ANCHOR_RE.fullmatch(name):
        return None, raw
    rest = raw[len(head) :]
    rest = LEADING_MENTION_SEPARATORS.sub("", rest).strip()
    return name, rest or raw


def assignee_pick_for_count(count: int) -> MentionPick:
    """При нескольких @user в группе — ближайший к тайм-фразе, иначе первый."""
    return "nearest_time" if count > 1 else "first"


def format_assignee_pick_note(
    source_text: str,
    *,
    chosen: str,
    candidates: list[str],
) -> str | None:
    """Пояснение автовыбора assignee — показываем в confirm, если @user несколько."""
    others = [u for u in candidates if u.lower() != chosen.lower()]
    if len(candidates) <= 1:
        return None
    anchor_match = _TIME_ANCHOR_RE.search(source_text or "")
    if not anchor_match:
        if len(others) == 1:
            return f"ℹ️ Также @{others[0]} — взят @{chosen} (нет времени в фразе)."
        return (
            f"ℹ️ {len(candidates)} @user — взят @{chosen}. "
            "Добавь «через …» / «завтра в …» или оставь одного."
        )
    anchor = anchor_match.group(0)
    if len(others) == 1:
        return f"ℹ️ Также @{others[0]} — взят @{chosen} (ближе к «{anchor}»)."
    tags = ", ".join(f"@{u}" for u in others[:3])
    if len(others) > 3:
        tags += "…"
    return f"ℹ️ Взят @{chosen} (ближе к «{anchor}»). Ещё: {tags}."


def _resolve_pick(pick: MentionPick, span_count: int) -> MentionPick:
    if pick == "auto":
        return assignee_pick_for_count(span_count)
    return pick


def _pick_username(spans: list[tuple[int, int, str]], pick: MentionPick, source_text: str) -> str | None:
    if not spans:
        return None
    pick = _resolve_pick(pick, len(spans))
    if pick == "last":
        return spans[-1][2]
    if pick == "nearest_time":
        anchor = _time_anchor_index(source_text)
        if anchor is None:
            return spans[0][2]
        before = [item for item in spans if item[0] <= anchor]
        if before:
            return before[-1][2]
        return min(spans, key=lambda item: abs(item[0] - anchor))[2]
    return spans[0][2]


def _candidate_source_text(original: str, bot_username: str | None) -> tuple[str, bool]:
    starts_with_bot = strip_leading_bot_mention(original, bot_username) != original
    raw = strip_text_before_bot_mention(original, bot_username)
    has_mid_bot = raw != original and not starts_with_bot
    return raw, has_mid_bot


def extract_username_candidates(
    text: str,
    bot_username: str | None = None,
) -> tuple[list[str], str]:
    """
    Возвращает всех найденных @user (не бот) в порядке слева-направо + clean без @user.
    Нужен для A/B-логики выбора assignee на уровне вызывающего кода.
    """
    original = (text or "").strip()
    raw, has_mid_bot = _candidate_source_text(original, bot_username)

    spans = _user_mention_spans(raw, bot_username)
    if not spans and has_mid_bot:
        return [], original
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
    raw = text.strip()
    for pattern in (FOR_USER_PREFIX, USERNAME_PREFIX):
        match = pattern.match(raw)
        if not match:
            continue
        username = match.group(1)
        if _is_bot_mention(username, bot_username):
            return None, raw[match.end() :].strip()
        clean = raw[match.end() :].strip()
        return username, strip_all_user_mentions(clean, bot_username)
    return None, raw


def extract_username_anywhere(
    text: str,
    bot_username: str | None = None,
    *,
    pick: MentionPick = "auto",
) -> tuple[str | None, str]:
    """
    Выбор assignee из текста по варианту:
    - auto (default): первый @user, при нескольких — nearest_time
    - first: всегда первый @user слева
    - last: последний @user
    - nearest_time: ближайший к тайм-фразе (например, "завтра", "через", "в 10:00")
    """
    original = (text or "").strip()
    raw, has_mid_bot = _candidate_source_text(original, bot_username)
    spans = _user_mention_spans(raw, bot_username)
    if len(spans) <= 1:
        leading_user, leading_clean = extract_leading_username(raw, bot_username)
        if leading_user:
            return leading_user, leading_clean
    if not spans and has_mid_bot:
        return None, original
    if not spans:
        return None, raw
    clean = strip_all_user_mentions(raw, bot_username)
    return _pick_username(spans, pick, raw), clean


def _apply_entity_user_mentions(
    text: str,
    user_hits: list[tuple[int, int, str, int | None]],
) -> tuple[int | None, str | None]:
    """Выбор assignee из entities; при нескольких — nearest_time."""
    if not user_hits:
        return None, None
    if len(user_hits) == 1:
        _, _, username, user_id = user_hits[0]
        return user_id, username or None
    spans = [(start, start + length, username or f"\0{idx}") for idx, (start, length, username, _) in enumerate(user_hits)]
    pick = assignee_pick_for_count(len(spans))
    chosen = _pick_username(spans, pick, text)
    if not chosen:
        return None, None
    if chosen.startswith("\0"):
        idx = int(chosen[1:])
        _, _, username, user_id = user_hits[idx]
        return user_id, username or None
    chosen_id: int | None = None
    for _, _, username, user_id in user_hits:
        if username and username.lower() == chosen.lower():
            chosen_id = user_id
            break
    return chosen_id, chosen or None


def extract_mention_from_message(
    message: Message,
    *,
    bot_username: str | None = None,
    bot_id: int | None = None,
) -> tuple[int | None, str | None, str]:
    """Возвращает (telegram_user_id, username, очищенный текст). Упоминание бота пропускается."""
    raw, entities = _message_text_and_entities(message)
    if not raw:
        return None, None, raw

    text, phrase_start_py = _phrase_window(raw)

    clean = text
    mention_id: int | None = None
    mention_username: str | None = None
    removed_spans: list[tuple[int, int]] = []
    user_hits: list[tuple[int, int, str, int | None]] = []

    if entities:
        for entity in sorted(entities, key=lambda e: e.offset):
            py_start, py_end = _entity_span_py(raw, entity)
            if py_end <= phrase_start_py:
                continue

            rel_start = max(0, py_start - phrase_start_py)
            py_length = py_end - py_start

            if entity.type == "text_mention" and entity.user:
                if entity.user.is_bot or _is_bot_mention(
                    entity.user.username,
                    bot_username,
                    user_id=entity.user.id,
                    bot_id=bot_id,
                ):
                    removed_spans.append((rel_start, py_length))
                    continue
                visible = raw[py_start:py_end].lstrip("@")
                username = entity.user.username or visible or ""
                user_hits.append((rel_start, py_length, username, entity.user.id))
                removed_spans.append((rel_start, py_length))
                continue

            if entity.type == "mention":
                username = raw[py_start + 1 : py_end]
                if _is_bot_mention(username, bot_username):
                    removed_spans.append((rel_start, py_length))
                    continue
                user_hits.append((rel_start, py_length, username, None))
                removed_spans.append((rel_start, py_length))
                continue

        if user_hits:
            mention_id, mention_username = _apply_entity_user_mentions(text, user_hits)

        if removed_spans:
            clean = _remove_spans(text, removed_spans)
            clean = strip_all_user_mentions(clean, bot_username)

    if mention_username is None and mention_id is None:
        clean = strip_text_before_bot_mention(clean, bot_username)
        username, clean = extract_username_anywhere(clean, bot_username, pick="auto")
        if username:
            mention_username = username
        else:
            plain_name, plain_clean = _extract_leading_plain_name(clean)
            if plain_name:
                mention_username = plain_name
                clean = plain_clean

    clean = strip_all_bot_mentions(clean or text, bot_username)
    clean = _normalize_phrase_whitespace(clean)
    return mention_id, mention_username, clean
