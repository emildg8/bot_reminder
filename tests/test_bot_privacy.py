from bot.services.bot_privacy import (
    format_group_at_manual_warning,
    format_group_privacy_admin_warning,
    format_group_privacy_status,
)


def test_privacy_warning_when_enabled():
    text = format_group_privacy_admin_warning(can_read_all_group_messages=False)
    assert text is not None
    assert "Group Privacy" in text
    assert "Turn off" in text


def test_no_warning_when_disabled():
    assert format_group_privacy_admin_warning(can_read_all_group_messages=True) is None
    assert format_group_privacy_admin_warning(can_read_all_group_messages=None) is None


def test_privacy_status_lines():
    assert "выкл" in format_group_privacy_status(can_read_all_group_messages=True)
    assert "вкл" in format_group_privacy_status(can_read_all_group_messages=False)


def test_manual_at_warning():
    assert "вручную" in format_group_at_manual_warning()
