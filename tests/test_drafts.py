from datetime import datetime

from bot.services.drafts import pop_draft, pop_edit_pending, set_edit_pending, store_draft
from bot.services.nlp.schemas import ParsedReminder


def _parsed() -> ParsedReminder:
    return ParsedReminder(
        text="тест",
        kind="once",
        run_at=datetime(2030, 1, 1, 12, 0),
    )


def test_store_and_pop_draft():
    draft_id = store_draft(1, _parsed(), mention_telegram_id=42, edit_reminder_id=7)
    entry = pop_draft(draft_id, 1)
    assert entry is not None
    assert entry.mention_telegram_id == 42
    assert entry.edit_reminder_id == 7
    assert pop_draft(draft_id, 1) is None


def test_edit_pending():
    set_edit_pending(5, 99)
    assert pop_edit_pending(5) == 99
    assert pop_edit_pending(5) is None
