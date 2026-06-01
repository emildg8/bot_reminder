from bot.texts.messages import format_assignee_compact, format_mention_assignee_line


def test_assignee_line_reply():
    line = format_mention_assignee_line(42, "ivan", resolved=True, source="reply")
    assert "↩️" in line
    assert "ответ на сообщение" in line
    assert "tg://user?id=42" in line


def test_assignee_compact_reply():
    line = format_assignee_compact(42, "ivan", source="reply")
    assert line.startswith("↩️")
    assert "ivan" in line


def test_format_created_with_assignee():
    from bot.texts.messages import format_created

    body = format_created(
        1,
        "завтра 14:00",
        "созвон",
        mention_user_id=42,
        mention_username="ivan",
        mention_source="reply",
    )
    assert "👤" in body or "↩️" in body
    assert "ivan" in body


def test_assignee_line_unresolved():
    line = format_mention_assignee_line(None, "ghost", resolved=False, source="text")
    assert "ghost" in line
    assert "не в этом чате" in line
