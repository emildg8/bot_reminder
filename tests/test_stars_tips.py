import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.db.repository import get_or_create_user, record_star_payment
from bot.handlers.payments import pre_checkout, successful_payment
from bot.services.stars_tips import tip_payload, tips_enabled


@pytest.mark.asyncio
async def test_stars_tip_thank_you(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.stars_tips_enabled", True)
    user_id = 77001
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")

    message = MagicMock()
    message.from_user.id = user_id
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
    assert "Спасибо" in message.answer.await_args[0][0]
    assert "100" in message.answer.await_args[0][0]


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
    monkeypatch.setattr("bot.handlers.payments.tips_enabled", lambda: True)
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = tip_payload(123, 50)
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_pre_checkout_wrong_user(monkeypatch):
    monkeypatch.setattr("bot.handlers.payments.tips_enabled", lambda: True)
    query = MagicMock()
    query.from_user.id = 123
    query.invoice_payload = tip_payload(999, 50)
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(
        ok=False, error_message="Платёж привязан к другому пользователю"
    )


def test_tips_disabled_by_default():
    assert tips_enabled() is False


def test_tip_payload_roundtrip():
    assert tip_payload(42, 100) == "tip:42:100"
