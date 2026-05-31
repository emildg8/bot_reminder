from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from bot.config import settings
from bot.services.nlp.llm_parser import parse_all_reminders
from bot.services.nlp.schemas import ParsedReminder


@pytest.mark.asyncio
async def test_llm_fallback_when_rules_empty(monkeypatch):
    monkeypatch.setattr(
        "bot.services.nlp.llm_parser.parse_all_with_rules",
        lambda text, timezone: [],
    )

    tz = ZoneInfo("Europe/Moscow")
    llm_result = ParsedReminder(
        text="созвон",
        kind="once",
        run_at=datetime.now(tz) + timedelta(hours=2),
    )

    async def fake_try_llm(client, model, user_text, timezone):
        return llm_result

    monkeypatch.setattr("bot.services.nlp.llm_parser._try_llm", fake_try_llm)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")

    results = await parse_all_reminders("сложная фраза без правил", "Europe/Moscow")
    assert len(results) == 1
    assert results[0].text == "созвон"


@pytest.mark.asyncio
async def test_llm_not_called_when_rules_match(monkeypatch):
    tz = ZoneInfo("Europe/Moscow")
    rule_result = [
        ParsedReminder(
            text="таблетки",
            kind="once",
            run_at=datetime.now(tz) + timedelta(minutes=30),
        )
    ]
    monkeypatch.setattr(
        "bot.services.nlp.llm_parser.parse_all_with_rules",
        lambda text, timezone: rule_result,
    )

    llm_mock = AsyncMock(return_value=None)
    monkeypatch.setattr("bot.services.nlp.llm_parser._try_llm", llm_mock)
    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    results = await parse_all_reminders("через 30 минут таблетки", "Europe/Moscow")
    assert results == rule_result
    llm_mock.assert_not_awaited()
