from bot.services.mention_parse import format_assignee_pick_note
from bot.texts.messages import (
    format_assignee_choice_prompt,
    format_assignee_preview_plain,
    format_collective_check_dm,
    format_mention_assignee_line,
)
from bot.services.chat_ctx import ChatKind
from bot.services.reminder_display import format_parsed_one_liner
from bot.services.nlp.schemas import ParsedReminder


def test_pick_note_nearest_time():
    note = format_assignee_pick_note(
        "@alice @bobby через час задача",
        chosen="bobby",
        candidates=["alice", "bobby"],
    )
    assert note is not None
    assert "bobby" in note
    assert "alice" in note
    assert "через" in note


def test_pick_note_no_time():
    note = format_assignee_pick_note(
        "@alice @bobby созвон",
        chosen="alice",
        candidates=["alice", "bobby"],
    )
    assert note is not None
    assert "нет времени" in note


def test_pick_note_single_user():
    assert (
        format_assignee_pick_note("через час", chosen="alice", candidates=["alice"])
        is None
    )


def test_mention_line_includes_pick_note():
    line = format_mention_assignee_line(
        1,
        "ivan",
        pick_note="ℹ️ Также @petr — выбран @ivan.",
    )
    assert "Кому" in line
    assert "ℹ️" in line


def test_collective_check_dm_preview():
    text = format_collective_check_dm(
        ChatKind.SUPERGROUP,
        "Team",
        preview="👤 @ivan · через 1 мин · тест",
    )
    assert "@ivan" in text
    assert "личке" in text


def test_parsed_one_liner():
    parsed = ParsedReminder(
        text="тест",
        kind="once",
        run_at=None,
        delay_seconds=60,
    )
    line = format_parsed_one_liner(parsed, "Europe/Moscow")
    assert "тест" in line
    assert "мин" in line


def test_assignee_preview_plain():
    assert format_assignee_preview_plain("ivan") == "👤 @ivan"
    assert format_assignee_preview_plain("ivan", source="reply").startswith("↩️")
    assert format_assignee_preview_plain("Emil") == "👤 Emil"
    assert format_assignee_preview_plain("Emil", resolved=False) == "👤 Emil?"


def test_assignee_choice_prompt_includes_task_preview():
    text = format_assignee_choice_prompt(
        ["alice", "bobby"],
        task_preview="📝 созвон",
    )
    assert "созвон" in text
    assert "@alice" in text
    assert "время не указано" in text
