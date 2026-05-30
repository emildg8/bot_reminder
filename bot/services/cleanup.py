"""Очистка in-memory кэшей."""

from __future__ import annotations

from bot.services.drafts import prune_expired as prune_drafts
from bot.services.pending_tasks import prune_expired_pending_tasks
from bot.services.search_ui import prune_expired_search_cache


def prune_all_caches() -> int:
    removed = prune_drafts()
    removed += prune_expired_pending_tasks()
    removed += prune_expired_search_cache()
    return removed
