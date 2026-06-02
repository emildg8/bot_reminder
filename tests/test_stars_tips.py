import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.db.repository import get_or_create_user, record_star_payment, set_user_tip_nudge_dismissed, set_user_tip_nudge_shown
from bot.handlers.menu import cmd_cancel
from bot.handlers.payments import cb_tip_pay, pre_checkout, successful_payment
from bot.handlers.tips import cb_tip_back, cb_tip_confirm, cb_tip_custom, handle_custom_tip_amount
from bot.services.chat_status import build_status_text
from bot.services.stars_tips import (
    deliver_tip_invoice,
    format_amount_out_of_range,
    format_custom_amount_invalid,
    format_thank_you,
    looks_like_reminder_phrase,
    looks_like_tip_amount,
    parse_tip_amount_input,
    pre_checkout_error,
    should_send_tip_nudge,
    text_has_letters,
    tip_payload,
    tips_enabled,
)
from bot.services.tip_custom_state import (
    clear_custom_amount,
    get_pending_confirm,
    is_pending_confirm,
    is_waiting_custom_amount,
    set_pending_confirm,
    start_custom_amount,
)


@pytest.mark.asyncio
async def test_stars_tip_thank_you(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77001
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")

    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.first_name = "Аня"
    message.from_user.username = "tester"
    message.chat.id = user_id
    message.successful_payment = MagicMock(
        currency="XTR",
        total_amount=100,
        invoice_payload=tip_payload(user_id, 100),
        telegram_payment_charge_id="charge_tip_1",
    )
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_message = AsyncMock()

    await successful_payment(message)
    message.answer.assert_awaited_once()
    text = message.answer.await_args[0][0]
    assert "Спасибо" in text
    assert "100" in text
    assert "Первый раз" in text


@pytest.mark.asyncio
async def test_stars_tip_repeat_shows_total(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77011
    await record_star_payment(
        patched_db,
        user_telegram_id=user_id,
        charge_id="old_charge",
        stars_amount=50,
        kind="tip",
    )

    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.first_name = "Аня"
    message.chat.id = user_id
    message.successful_payment = MagicMock(
        currency="XTR",
        total_amount=100,
        invoice_payload=tip_payload(user_id, 100),
        telegram_payment_charge_id="charge_tip_2",
    )
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_message = AsyncMock()

    await successful_payment(message)
    text = message.answer.await_args[0][0]
    assert "150" in text


@pytest.mark.asyncio
async def test_custom_amount_shows_confirm(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77003
    start_custom_amount(user_id)

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "75 ⭐"
    message.bot = MagicMock()
    message.answer = AsyncMock()

    await handle_custom_tip_amount(message)
    message.answer.assert_awaited_once()
    assert "75" in message.answer.await_args[0][0]
    assert is_pending_confirm(user_id)
    assert get_pending_confirm(user_id) == 75


@pytest.mark.asyncio
async def test_custom_amount_confirm_sends_invoice(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77009
    set_pending_confirm(user_id, 75)

    callback = MagicMock()
    callback.from_user.id = user_id
    callback.data = "tip:confirm:75"
    callback.message.chat.id = user_id
    callback.bot = MagicMock()
    callback.bot.send_invoice = AsyncMock()
    callback.bot.send_message = AsyncMock()
    callback.answer = AsyncMock()

    await cb_tip_confirm(callback)
    callback.bot.send_invoice.assert_awaited_once()
    assert not is_pending_confirm(user_id)


@pytest.mark.asyncio
async def test_custom_amount_phrase_passthrough(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77005
    start_custom_amount(user_id)

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "завтра в 14 созвон"
    message.bot = MagicMock()
    message.answer = AsyncMock()

    await handle_custom_tip_amount(message)
    message.answer.assert_not_awaited()
    assert not is_waiting_custom_amount(user_id)


@pytest.mark.asyncio
async def test_custom_amount_group_sends_dm(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77006
    group_id = -100123
    set_pending_confirm(user_id, 50)

    callback = MagicMock()
    callback.from_user.id = user_id
    callback.data = "tip:confirm:50"
    callback.message.chat.id = group_id
    callback.bot = MagicMock()
    callback.bot.send_invoice = AsyncMock()
    callback.bot.send_message = AsyncMock()
    callback.answer = AsyncMock()

    await cb_tip_confirm(callback)
    assert callback.bot.send_invoice.await_args.kwargs["chat_id"] == user_id
    assert "личку" in callback.bot.send_message.await_args[0][1].lower()


@pytest.mark.asyncio
async def test_cb_tip_pay_delivers_to_dm(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77007
    callback = MagicMock()
    callback.from_user.id = user_id
    callback.data = "tip:pay:50"
    callback.message.chat.id = -999
    callback.bot = MagicMock()
    callback.bot.send_invoice = AsyncMock()
    callback.bot.send_message = AsyncMock()
    callback.answer = AsyncMock()

    await cb_tip_pay(callback)
    assert callback.bot.send_invoice.await_args.kwargs["chat_id"] == user_id


def test_parse_tip_amount_input_variants():
    assert parse_tip_amount_input("75") == 75
    assert parse_tip_amount_input("75 ⭐") == 75
    assert parse_tip_amount_input("1 000") == 1000
    assert parse_tip_amount_input("abc") is None


def test_text_has_letters():
    assert text_has_letters("завтра")
    assert not text_has_letters("75 ⭐")


def test_looks_like_tip_amount():
    assert looks_like_tip_amount("75")
    assert not looks_like_tip_amount("завтра созвон")


@pytest.mark.asyncio
async def test_deliver_tip_invoice_dm_blocked(monkeypatch):
    from aiogram.exceptions import TelegramBadRequest

    bot = MagicMock()
    bot.send_invoice = AsyncMock(side_effect=TelegramBadRequest(method=MagicMock(), message="chat not found"))
    bot.send_message = AsyncMock()
    ok = await deliver_tip_invoice(bot, user_id=1, amount=50, reply_chat_id=-100)
    assert ok is False
    assert "/start" in bot.send_message.await_args[0][1]


def test_format_amount_out_of_range():
    text = format_amount_out_of_range(99999)
    assert "99999" in text
    assert "2500" in text


def test_looks_like_reminder_phrase():
    assert looks_like_reminder_phrase("завтра в 14 созвон")
    assert looks_like_reminder_phrase("завтра")
    assert not looks_like_reminder_phrase("abc")
    assert not looks_like_reminder_phrase("75 ⭐")


@pytest.mark.asyncio
async def test_custom_amount_non_numeric_stays_waiting(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77008
    start_custom_amount(user_id)

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "abc"
    message.bot = MagicMock()
    message.answer = AsyncMock()

    await handle_custom_tip_amount(message)
    message.answer.assert_awaited_once()
    assert is_waiting_custom_amount(user_id)
    assert "число" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_custom_amount_single_reminder_word_passthrough(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77013
    start_custom_amount(user_id)

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "завтра"
    message.bot = MagicMock()
    message.answer = AsyncMock()

    await handle_custom_tip_amount(message)
    message.answer.assert_not_awaited()
    assert not is_waiting_custom_amount(user_id)


@pytest.mark.asyncio
async def test_custom_amount_out_of_range(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77004
    start_custom_amount(user_id)

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "999999"
    message.bot = MagicMock()
    message.answer = AsyncMock()

    await handle_custom_tip_amount(message)
    message.answer.assert_awaited_once()
    assert "диапазон" in message.answer.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_duplicate_charge_idempotent(patched_db):
    recorded = await record_star_payment(
        patched_db,
        user_telegram_id=77002,
        charge_id="dup_charge",
        stars_amount=50,
        kind="tip",
    )
    assert recorded is not None
    again = await record_star_payment(
        patched_db,
        user_telegram_id=77002,
        charge_id="dup_charge",
        stars_amount=50,
        kind="tip",
    )
    assert again is None


@pytest.mark.asyncio
async def test_pre_checkout_ok(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = tip_payload(123, 50)
    query.total_amount = 50
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_pre_checkout_wrong_user(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = tip_payload(999, 50)
    query.total_amount = 50
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(
        ok=False, error_message="Платёж привязан к другому пользователю"
    )


def test_tips_disabled_by_default():
    assert tips_enabled() is False


def test_pre_checkout_error_ok(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    assert pre_checkout_error(tip_payload(1, 50), payer_id=1, total_amount=50) is None


def test_format_thank_you_total():
    text = format_thank_you(100, first_name="Ира", total_tips=250)
    assert "250" in text
    assert "emildg8" in text


@pytest.mark.asyncio
async def test_pre_checkout_non_tip_passes(monkeypatch):
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = "other:product:1"
    query.total_amount = 100
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_successful_payment_when_tips_disabled(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    user_id = 77012
    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.first_name = "Test"
    message.chat.id = user_id
    message.successful_payment = MagicMock(
        currency="XTR",
        total_amount=50,
        invoice_payload=tip_payload(user_id, 50),
        telegram_payment_charge_id="charge_disabled",
    )
    message.answer = AsyncMock()
    message.bot = MagicMock()

    await successful_payment(message)
    message.answer.assert_awaited_once()
    assert "Спасибо" in message.answer.await_args[0][0]


@pytest.mark.asyncio
async def test_tip_nudge_respects_once_flag(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_once", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_min_dones", 0)
    user_id = 88010
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    await set_user_tip_nudge_shown(patched_db, user_id)
    assert await should_send_tip_nudge(patched_db, user_id) is False


@pytest.mark.asyncio
async def test_cb_tip_custom_starts_waiting(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 88001
    clear_custom_amount(user_id)
    callback = MagicMock()
    callback.from_user.id = user_id
    callback.answer = AsyncMock()
    callback.message.answer = AsyncMock()
    await cb_tip_custom(callback)
    assert is_waiting_custom_amount(user_id)


@pytest.mark.asyncio
async def test_cb_tip_back_clears_waiting(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 88002
    start_custom_amount(user_id)
    callback = MagicMock()
    callback.from_user.id = user_id
    callback.message = MagicMock()
    callback.message.from_user = callback.from_user
    callback.message.chat.id = user_id
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    await cb_tip_back(callback)
    assert not is_waiting_custom_amount(user_id)
    callback.message.answer.assert_awaited_once()


def test_pre_checkout_error_when_tips_disabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    assert pre_checkout_error(tip_payload(1, 50), payer_id=1, total_amount=50) is None


@pytest.mark.asyncio
async def test_pre_checkout_ok_when_tips_disabled(monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = tip_payload(123, 50)
    query.total_amount = 50
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_tip_nudge_skips_donors(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_once", False)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_min_dones", 0)
    user_id = 88020
    await record_star_payment(
        patched_db,
        user_telegram_id=user_id,
        charge_id="donor_1",
        stars_amount=25,
        kind="tip",
    )
    assert await should_send_tip_nudge(patched_db, user_id) is False


@pytest.mark.asyncio
async def test_tip_nudge_dismissed_respects_cooldown(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_once", False)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_days", 14)
    monkeypatch.setattr("bot.config.settings.stars_tip_nudge_min_dones", 0)
    user_id = 88021
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    await set_user_tip_nudge_dismissed(patched_db, user_id)
    assert await should_send_tip_nudge(patched_db, user_id) is False


@pytest.mark.asyncio
async def test_status_shows_donor_when_tips_disabled(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", False)
    user_id = 88022
    await record_star_payment(
        patched_db,
        user_telegram_id=user_id,
        charge_id="donor_status",
        stars_amount=100,
        kind="tip",
    )
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.chat.type = "private"
    bot = MagicMock()
    text = await build_status_text(bot, message)
    assert "поддержал" in text.lower()
    assert "100" in text


@pytest.mark.asyncio
async def test_cancel_in_tip_mode(patched_db, monkeypatch):
    user_id = 88023
    start_custom_amount(user_id)
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.answer = AsyncMock()
    await cmd_cancel(message)
    assert not is_waiting_custom_amount(user_id)
    assert "stars" in message.answer.await_args[0][0].lower()


def test_format_custom_amount_invalid_hint():
    text = format_custom_amount_invalid("???")
    assert "число" in text.lower()
    assert "напоминан" in text.lower()
