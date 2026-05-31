"""Относительные «через N …» → delay_seconds для подтверждения."""

from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.services.nlp.schemas import ParsedReminder

_RELATIVE_TRIGGER = re.compile(r"\bчерез\b", re.IGNORECASE)


def apply_relative_delay(
    parsed: ParsedReminder,
    user_text: str,
    timezone: str,
) -> ParsedReminder:
    if parsed.kind != "once" or parsed.run_at is None:
        return parsed
    if not _RELATIVE_TRIGGER.search(user_text):
        return parsed
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    run_at = parsed.run_at
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=tz)
    delta = int((run_at.astimezone(tz) - now).total_seconds())
    if delta <= 0:
        return parsed
    parsed.delay_seconds = delta
    return parsed
