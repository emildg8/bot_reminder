from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import uuid

from bot.services.nlp.schemas import ParsedReminder

logger = logging.getLogger(__name__)

DRAFT_TTL = timedelta(hours=1)
EDIT_PENDING_TTL = timedelta(hours=2)
SEARCH_PENDING_TTL = timedelta(minutes=10)


@dataclass
class DraftEntry:
    parsed: ParsedReminder
    user_id: int
    created_at: datetime
    mention_telegram_id: int | None = None
    mention_provided: bool = False
    edit_reminder_id: int | None = None


_draft_entries: dict[str, DraftEntry] = {}
_edit_pending: dict[int, tuple[int, datetime]] = {}
_search_pending: dict[int, datetime] = {}


def store_draft(
    user_id: int,
    parsed: ParsedReminder,
    mention_telegram_id: int | None = None,
    mention_provided: bool = False,
    edit_reminder_id: int | None = None,
) -> str:
    prune_expired()
    draft_id = uuid.uuid4().hex[:12]
    _draft_entries[draft_id] = DraftEntry(
        parsed=parsed,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        mention_telegram_id=mention_telegram_id,
        mention_provided=mention_provided,
        edit_reminder_id=edit_reminder_id,
    )
    return draft_id


def get_draft(draft_id: str, user_id: int) -> DraftEntry | None:
    entry = _draft_entries.get(draft_id)
    if entry is None or entry.user_id != user_id:
        return None
    if datetime.now(timezone.utc) - entry.created_at > DRAFT_TTL:
        _draft_entries.pop(draft_id, None)
        return None
    return entry


def pop_draft(draft_id: str, user_id: int) -> DraftEntry | None:
    entry = _draft_entries.pop(draft_id, None)
    if entry is None or entry.user_id != user_id:
        return None
    return entry


def discard_draft(draft_id: str, user_id: int | None = None) -> None:
    entry = _draft_entries.get(draft_id)
    if entry is not None and user_id is not None and entry.user_id != user_id:
        return
    _draft_entries.pop(draft_id, None)


def set_edit_pending(user_id: int, reminder_id: int) -> None:
    _edit_pending[user_id] = (reminder_id, datetime.now(timezone.utc))


def pop_edit_pending(user_id: int) -> int | None:
    item = _edit_pending.pop(user_id, None)
    if item is None:
        return None
    reminder_id, created_at = item
    if datetime.now(timezone.utc) - created_at > EDIT_PENDING_TTL:
        return None
    return reminder_id


def clear_edit_pending(user_id: int) -> None:
    _edit_pending.pop(user_id, None)


def set_search_pending(user_id: int) -> None:
    _search_pending[user_id] = datetime.now(timezone.utc)


def pop_search_pending(user_id: int) -> bool:
    created_at = _search_pending.pop(user_id, None)
    if created_at is None:
        return False
    if datetime.now(timezone.utc) - created_at > SEARCH_PENDING_TTL:
        return False
    return True


def clear_search_pending(user_id: int) -> None:
    _search_pending.pop(user_id, None)


def prune_expired() -> int:
    """Удаляет устаревшие черновики и режим редактирования. Возвращает число удалённых."""
    now = datetime.now(timezone.utc)
    removed = 0

    for draft_id, entry in list(_draft_entries.items()):
        if now - entry.created_at > DRAFT_TTL:
            _draft_entries.pop(draft_id, None)
            removed += 1

    for user_id, (_, created_at) in list(_edit_pending.items()):
        if now - created_at > EDIT_PENDING_TTL:
            _edit_pending.pop(user_id, None)
            removed += 1

    for user_id, created_at in list(_search_pending.items()):
        if now - created_at > SEARCH_PENDING_TTL:
            _search_pending.pop(user_id, None)
            removed += 1

    if removed:
        logger.debug("Pruned %s expired draft/edit entries", removed)
    return removed
