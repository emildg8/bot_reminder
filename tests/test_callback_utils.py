from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest

from bot.services.callback_utils import safe_callback_answer


@pytest.mark.asyncio
async def test_safe_callback_answer_ok():
    callback = MagicMock()
    callback.answer = AsyncMock()
    await safe_callback_answer(callback, "ok", show_alert=True)
    callback.answer.assert_awaited_once_with("ok", show_alert=True)


@pytest.mark.asyncio
async def test_safe_callback_answer_ignores_bad_request():
    callback = MagicMock()
    callback.answer = AsyncMock(side_effect=TelegramBadRequest(method="answerCallbackQuery", message="expired"))
    await safe_callback_answer(callback)
