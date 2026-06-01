from bot.services.admin_audit import format_admin_log, log_admin_action


def test_admin_log_ring():
    for i in range(50):
        log_admin_action(1, f"action-{i}")
    text = format_admin_log(limit=5)
    assert "action-49" in text
    assert "action-40" not in text
