#!/usr/bin/env python3
"""Smoke group assignee: парсинг @бот + @user (без pytest).

Запуск: python scripts/smoke_group_mentions.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.services.assignee_prompt import should_offer_assignee_choice  # noqa: E402
from bot.services.collective_preview import build_assignee_choice_task_preview  # noqa: E402
from bot.services.mention_parse import (  # noqa: E402
    assignee_pick_for_count,
    extract_leading_username,
    extract_mention_from_message,
    extract_username_anywhere,
    extract_username_candidates,
    format_assignee_pick_note,
    strip_leading_bot_mention,
)
from bot.services.nlp.schemas import ParsedReminder  # noqa: E402


def _ok(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    errors: list[str] = []
    bot = "break_remind_bot"

    cases_strip = (
        ("@break_remind_bot через минуту тест", "через минуту тест"),
        ("@break_remind_bot@mokew2222 через минуту тест", "@mokew2222 через минуту тест"),
        ("@break_remind_bot + @mokew2222 через минуту тест", "@mokew2222 через минуту тест"),
    )
    for raw, want in cases_strip:
        got = strip_leading_bot_mention(raw, bot)
        _ok(got == want, f"strip({raw!r}) = {got!r}, want {want!r}", errors)

    _ok(assignee_pick_for_count(2) == "nearest_time", "assignee_pick_for_count(2)", errors)
    username, clean = extract_username_anywhere(
        "@break_remind_bot @alice @bobby через час задача",
        bot_username=bot,
    )
    _ok(username == "bobby", f"multi auto username={username!r}", errors)
    _ok(clean == "через час задача", f"multi auto clean={clean!r}", errors)
    username_last, clean_last = extract_username_anywhere(
        "@break_remind_bot @alice @bobby через час задача",
        bot_username=bot,
        pick="last",
    )
    _ok(username_last == "bobby", f"pick=last username={username_last!r}", errors)
    _ok(clean_last == "через час задача", f"pick=last clean={clean_last!r}", errors)
    username_time, clean_time = extract_username_anywhere(
        "@break_remind_bot @alice @bobby завтра в 10:00 созвон",
        bot_username=bot,
        pick="nearest_time",
    )
    _ok(username_time == "bobby", f"pick=nearest_time username={username_time!r}", errors)
    _ok(clean_time == "завтра в 10:00 созвон", f"pick=nearest_time clean={clean_time!r}", errors)
    usernames, clean_candidates = extract_username_candidates(
        "@break_remind_bot @alice @bobby через час задача",
        bot_username=bot,
    )
    _ok(usernames == ["alice", "bobby"], f"candidates usernames={usernames!r}", errors)
    _ok(clean_candidates == "через час задача", f"candidates clean={clean_candidates!r}", errors)

    message = SimpleNamespace(
        text="@break_remind_bot — @mokew2222 через минуту тест",
        caption=None,
        entities=[],
    )
    _, mention_username, clean_msg = extract_mention_from_message(
        message,
        bot_username=bot,
        bot_id=1,
    )
    _ok(mention_username == "mokew2222", f"full parse user={mention_username!r}", errors)
    _ok(clean_msg == "через минуту тест", f"full parse clean={clean_msg!r}", errors)

    msg_multi = SimpleNamespace(
        text="@break_remind_bot @alice @bobby завтра в 10:00 созвон",
        caption=None,
        entities=[],
    )
    _, multi_user, multi_clean = extract_mention_from_message(
        msg_multi,
        bot_username=bot,
        bot_id=1,
    )
    _ok(multi_user == "bobby", f"multi no-entities user={multi_user!r}", errors)
    _ok(multi_clean == "завтра в 10:00 созвон", f"multi no-entities clean={multi_clean!r}", errors)

    username, clean = extract_username_anywhere("для @alice через час задача")
    _ok(username == "alice" and clean == "через час задача", f"для @user {username!r}", errors)

    username, clean = extract_leading_username("напомни @alice через час задача")
    _ok(username == "alice" and clean == "через час задача", f"напомни @user {username!r}", errors)

    note = format_assignee_pick_note(
        "@bot @alice @bobby через час задача",
        chosen="bobby",
        candidates=["alice", "bobby"],
    )
    _ok(note is not None and "bobby" in note, "pick_note multi", errors)

    username, clean = extract_username_anywhere("@alice,через час задача")
    _ok(username == "alice" and clean == "через час задача", f"comma sep {username!r} {clean!r}", errors)

    _ok(
        should_offer_assignee_choice(["alice", "bobby"], "созвон"),
        "should_offer multi @ no time",
        errors,
    )
    _ok(
        not should_offer_assignee_choice(["alice", "bobby"], "через час созвон"),
        "should not offer when time anchor",
        errors,
    )
    preview = build_assignee_choice_task_preview(
        [ParsedReminder(text="созвон", kind="once", delay_seconds=3600, run_at=None)]
    )
    _ok(preview == "📝 созвон", f"assignee task preview {preview!r}", errors)

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("smoke_group_mentions: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
