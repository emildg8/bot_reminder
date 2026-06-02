"""Confirm-карточки в collective: полная карточка в личку, в чат — краткая подсказка."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from bot.services.chat_ctx import ChatKind
from bot.texts.messages import (
    format_collective_check_dm,
    format_collective_dm_confirm_header,
    format_collective_dm_failed_fallback,
)

logger = logging.getLogger(__name__)


async def send_collective_confirm(
    bot: Bot,
    *,
    user_id: int,
    collective_chat_id: int,
    collective_kind: ChatKind,
    chat_title: str | None,
    body: str,
    reply_markup: InlineKeyboardMarkup,
    group_preview: str | None = None,
) -> bool:
    """Отправляет confirm в личку; в collective — короткую подсказку. False → fallback в чат."""
    header = format_collective_dm_confirm_header(collective_kind, chat_title)
    dm_body = header + body
    try:
        await bot.send_message(user_id, dm_body, reply_markup=reply_markup)
    except Exception as exc:
        logger.warning(
            "Cannot DM confirm to user %s for chat %s: %s",
            user_id,
            collective_chat_id,
            exc,
        )
        return False

    try:
        await bot.send_message(
            collective_chat_id,
            format_collective_check_dm(
                collective_kind,
                chat_title,
                preview=group_preview,
            ),
        )
    except Exception as exc:
        logger.warning("Cannot send collective check-dm hint to %s: %s", collective_chat_id, exc)
    return True


async def send_collective_duplicate_confirm(
    bot: Bot,
    *,
    user_id: int,
    collective_chat_id: int,
    collective_kind: ChatKind,
    chat_title: str | None,
    body: str,
    reply_markup: InlineKeyboardMarkup,
) -> bool:
    return await send_collective_confirm(
        bot,
        user_id=user_id,
        collective_chat_id=collective_chat_id,
        collective_kind=collective_kind,
        chat_title=chat_title,
        body=body,
        reply_markup=reply_markup,
    )


def collective_dm_failed_suffix(bot_username: str | None) -> str:
    return "\n\n" + format_collective_dm_failed_fallback(bot_username)
