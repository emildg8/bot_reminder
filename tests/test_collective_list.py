import pytest

from bot.services.reminders_ui import build_list_message


@pytest.mark.asyncio
async def test_collective_list_shows_own_edit_buttons(monkeypatch):
    class Reminder:
        def __init__(self, rid: int, owner: int):
            self.id = rid
            self.created_by_telegram_id = owner
            self.text = "test"
            self.kind = "once"
            self.next_run_at = None
            self.timezone = "Europe/Moscow"
            self.is_active = True
            self.interval_seconds = None
            self.daily_time = None
            self.weekdays_mask = None
            self.mention_telegram_id = None

    async def fake_paused(_session, _chat_id):
        return False

    async def fake_active(_session, chat_id):
        return [Reminder(1, 100), Reminder(2, 200)]

    monkeypatch.setattr("bot.services.reminders_ui.is_chat_paused", fake_paused)
    monkeypatch.setattr("bot.services.reminders_ui.get_active_chat_reminders", fake_active)

    text, keyboard = await build_list_message(
        -100123,
        viewer_id=100,
        page=0,
        source_chat_id=-100123,
    )
    assert "/delete" in text
    assert "свои" in text
    assert keyboard is not None
    callbacks = [
        btn.callback_data
        for row in keyboard.inline_keyboard
        for btn in row
        if btn.callback_data
    ]
    assert "edit:1" in callbacks
    assert "del_confirm:1" in callbacks
    assert "edit:2" not in callbacks
    assert "del_confirm:2" not in callbacks
