import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from bot.db.repository import get_or_create_user, record_star_payment, set_user_pro
from bot.handlers.payments import pre_checkout, successful_payment
from bot.services.subscription import (
    compute_pro_expiry,
    is_pro_user,
    pro_invoice_payload,
    stars_payments_active,
)


@pytest.mark.asyncio
async def test_stars_payment_grants_pro(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.monetization_enabled", True)
    monkeypatch.setattr("bot.config.settings.stars_payments_enabled", True)
    user_id = 77001
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")

    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.successful_payment = MagicMock(
        currency="XTR",
        total_amount=250,
        telegram_payment_charge_id="charge_test_1",
    )
    message.answer = AsyncMock()

    await successful_payment(message)
    message.answer.assert_awaited_once()
    assert "Pro активирован" in message.answer.await_args[0][0]

    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert is_pro_user(user, user_id) is True
    assert user.pro_expires_at is not None


@pytest.mark.asyncio
async def test_duplicate_charge_idempotent(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.monetization_enabled", True)
    recorded = await record_star_payment(
        patched_db,
        user_telegram_id=77002,
        charge_id="dup_charge",
        stars_amount=250,
    )
    assert recorded is not None
    again = await record_star_payment(
        patched_db,
        user_telegram_id=77002,
        charge_id="dup_charge",
        stars_amount=250,
    )
    assert again is None


@pytest.mark.asyncio
async def test_pre_checkout_ok(monkeypatch):
    monkeypatch.setattr("bot.handlers.payments.stars_payments_active", lambda: True)
    query = MagicMock()
    query.invoice_payload = pro_invoice_payload(123)
    query.answer = AsyncMock()
    await pre_checkout(query)
    query.answer.assert_awaited_once_with(ok=True)


@pytest.mark.asyncio
async def test_pro_expiry_revokes(patched_db, monkeypatch):
    monkeypatch.setattr("bot.config.settings.monetization_enabled", True)
    user_id = 77003
    await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    past = datetime(2020, 1, 1, tzinfo=timezone.utc)
    await set_user_pro(patched_db, user_id, is_pro=True, pro_expires_at=past)
    user = await get_or_create_user(patched_db, user_id, "Europe/Moscow")
    assert is_pro_user(user, user_id) is False


def test_stars_payments_requires_both_flags(monkeypatch):
    monkeypatch.setattr("bot.config.settings.monetization_enabled", False)
    monkeypatch.setattr("bot.config.settings.stars_payments_enabled", True)
    assert stars_payments_active() is False
    monkeypatch.setattr("bot.config.settings.monetization_enabled", True)
    assert stars_payments_active() is True


def test_compute_pro_expiry():
    base = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    exp = compute_pro_expiry(base)
    assert exp > base
