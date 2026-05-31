"""Глобальная обработка необработанных ошибок хендлеров."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.services.callback_utils import safe_callback_answer

logger = logging.getLogger(__name__)
router = Router()


@router.error()
async def on_handler_error(event: ErrorEvent) -> bool:
    logger.exception("Unhandled handler error: %s", event.exception)

    update = event.update
    if update.callback_query:
        await safe_callback_answer(
            update.callback_query,
            "⚠️ Не удалось выполнить. Попробуй ещё раз или /help.",
            show_alert=True,
        )
    elif update.message:
        try:
            await update.message.answer("⚠️ Произошла ошибка. Попробуй /ping или /help.")
        except Exception:
            pass

    return True
