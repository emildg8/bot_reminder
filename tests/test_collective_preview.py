from datetime import datetime
from zoneinfo import ZoneInfo

from bot.services.collective_preview import (
    build_assignee_choice_task_preview,
    build_group_confirm_preview,
)
from bot.services.nlp.schemas import ParsedReminder


def test_build_assignee_choice_task_preview():
    parsed = ParsedReminder(text="созвон", kind="once", delay_seconds=3600, run_at=None)
    assert build_assignee_choice_task_preview([parsed]) == "📝 созвон"
    assert build_assignee_choice_task_preview([]) is None


def test_build_group_confirm_preview_with_assignee():
    parsed = ParsedReminder(
        text="тест",
        kind="once",
        delay_seconds=60,
        run_at=None,
    )
    preview = build_group_confirm_preview(
        [parsed],
        "Europe/Moscow",
        mention_username="ivan",
        mention_source="text",
    )
    assert preview is not None
    assert "@ivan" in preview
    assert "тест" in preview
    assert "мин" in preview


def test_build_group_confirm_preview_unresolved_assignee():
    parsed = ParsedReminder(text="тест", kind="once", delay_seconds=60, run_at=None)
    preview = build_group_confirm_preview(
        [parsed],
        "Europe/Moscow",
        mention_username="ghost",
        mention_source="text",
        mention_resolved=False,
    )
    assert preview is not None
    assert "@ghost?" in preview


def test_build_group_confirm_preview_batch():
    tz = ZoneInfo("Europe/Moscow")
    items = [
        ParsedReminder(text="a", kind="once", run_at=datetime(2030, 1, 1, 10, 0, tzinfo=tz)),
        ParsedReminder(text="b", kind="once", run_at=datetime(2030, 1, 2, 10, 0, tzinfo=tz)),
    ]
    preview = build_group_confirm_preview(items, "Europe/Moscow", mention_username=None, mention_source=None)
    assert preview == "2 напоминания"
