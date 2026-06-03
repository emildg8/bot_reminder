"""Краткое превью напоминания для сообщения в группе до confirm в личке."""

from __future__ import annotations

from bot.services.nlp.schemas import ParsedReminder
from bot.services.reminder_display import format_parsed_one_liner
from bot.texts.messages import format_assignee_preview_plain


def build_group_confirm_preview(
    parsed_items: list[ParsedReminder],
    timezone: str,
    *,
    mention_username: str | None,
    mention_source: str | None,
    mention_resolved: bool = True,
) -> str | None:
    if not parsed_items:
        return None
    when_part = (
        format_parsed_one_liner(parsed_items[0], timezone)
        if len(parsed_items) == 1
        else f"{len(parsed_items)} напоминания"
    )
    assignee_part = format_assignee_preview_plain(
        mention_username,
        source=mention_source,
        resolved=mention_resolved,
    )
    parts = [str(p) for p in (assignee_part, when_part) if p]
    return " · ".join(parts) if parts else None


def build_assignee_choice_task_preview(
    parsed_items: list[ParsedReminder],
) -> str | None:
    """Кратко, что напомнить, пока пользователь выбирает assignee."""
    if not parsed_items:
        return None
    if len(parsed_items) == 1:
        text = str(getattr(parsed_items[0], "text", None) or "").strip()
        if not text:
            return None
        if len(text) > 48:
            text = text[:45] + "…"
        return f"📝 {text}"
    return f"📝 {len(parsed_items)} напоминания"
