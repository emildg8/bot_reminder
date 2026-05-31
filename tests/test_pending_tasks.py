from bot.services.pending_tasks import clear_pending_task, pop_pending_task, store_pending_task


def test_pending_task_with_edit_id():
    store_pending_task(42, "почистить зубы", edit_reminder_id=7)
    entry = pop_pending_task(42)
    assert entry is not None
    assert entry.text == "почистить зубы"
    assert entry.edit_reminder_id == 7


def test_pending_task_create_only():
    store_pending_task(99, "созвон")
    entry = pop_pending_task(99)
    assert entry is not None
    assert entry.edit_reminder_id is None


def test_clear_pending_task():
    store_pending_task(7, "тест")
    clear_pending_task(7)
    assert pop_pending_task(7) is None
