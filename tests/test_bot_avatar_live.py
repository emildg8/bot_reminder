"""Интеграционный тест загрузки аватарки (только с реальным BOT_TOKEN)."""

import os

import pytest

from scripts.set_bot_avatar import is_plausible_bot_token, run_set_and_verify


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_avatar_live() -> None:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not is_plausible_bot_token(token):
        pytest.skip("Set valid BOT_TOKEN for live avatar upload test")

    await run_set_and_verify(token)
