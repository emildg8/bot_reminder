import pytest

from bot.db.repository import complete_user_onboarding, get_or_create_user
from bot.handlers.start import onboarding_callback, cmd_start
from bot.services.onboarding import onboarding_step_text
from bot.texts.messages import format_developer_made_by_line
from tests.callback_helpers import make_bot, make_callback, make_message, patch_create_flow


@pytest.mark.asyncio
async def test_onboarding_step_text_has_three_steps():
    assert "Шаг 1" in onboarding_step_text(1)
    assert "Шаг 2" in onboarding_step_text(2)
    assert "Шаг 3" in onboarding_step_text(3)


@pytest.mark.asyncio
async def test_new_user_gets_tour_after_timezone(patched_db, monkeypatch):
    user_id = 9700
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    user.timezone_confirmed = True
    user.onboarding_done = False
    await patched_db.commit()

    message = make_message(user_id)
    message.text = "/start"
    await cmd_start(message)

    body = message.answer.await_args_list[-1][0][0]
    assert "Шаг 1" in body


@pytest.mark.asyncio
async def test_onboarding_skip_marks_done(patched_db):
    user_id = 9701
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    user.onboarding_done = False
    await patched_db.commit()

    callback = make_callback("onb:skip", user_id)
    await onboarding_callback(callback, make_bot())

    refreshed = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert refreshed.onboarding_done is True
    assert callback.message.answer.await_count >= 2
    bodies = [call[0][0] for call in callback.message.answer.await_args_list]
    assert any(format_developer_made_by_line() in b for b in bodies)


@pytest.mark.asyncio
async def test_onboarding_next_advances_step(patched_db):
    user_id = 9702
    callback = make_callback("onb:next:2", user_id)
    await onboarding_callback(callback, make_bot())

    body = callback.message.edit_text.await_args[0][0]
    assert "Шаг 2" in body


@pytest.mark.asyncio
async def test_onboarding_try_runs_example(patched_db, monkeypatch):
    user_id = 9703
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    user.onboarding_done = False
    await patched_db.commit()

    callback = make_callback("onb:try", user_id)
    patch_create_flow(monkeypatch)
    await onboarding_callback(callback, make_bot())

    refreshed = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert refreshed.onboarding_done is True
    assert callback.message.edit_reply_markup.await_count == 1


@pytest.mark.asyncio
async def test_onboarding_restart_private(patched_db):
    callback = make_callback("onb:restart", user_id=501, chat_id=501)
    callback.message.answer = __import__("unittest").mock.AsyncMock()
    await onboarding_callback(callback, make_bot())
    callback.message.answer.assert_awaited()
    body = callback.message.answer.await_args[0][0]
    assert "Шаг 1" in body


@pytest.mark.asyncio
async def test_complete_user_onboarding_repo(patched_db):
    user_id = 9704
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert user.onboarding_done is False

    await complete_user_onboarding(patched_db, user)
    refreshed = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert refreshed.onboarding_done is True
