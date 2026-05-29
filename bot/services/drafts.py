from dataclasses import dataclass
import uuid

from bot.services.nlp.schemas import ParsedReminder


@dataclass
class DraftEntry:
    parsed: ParsedReminder
    user_id: int


_draft_entries: dict[str, DraftEntry] = {}


def store_draft(user_id: int, parsed: ParsedReminder) -> str:
    draft_id = uuid.uuid4().hex[:12]
    _draft_entries[draft_id] = DraftEntry(parsed=parsed, user_id=user_id)
    return draft_id


def pop_draft(draft_id: str, user_id: int) -> ParsedReminder | None:
    entry = _draft_entries.pop(draft_id, None)
    if entry is None or entry.user_id != user_id:
        return None
    return entry.parsed


def discard_draft(draft_id: str) -> None:
    _draft_entries.pop(draft_id, None)
