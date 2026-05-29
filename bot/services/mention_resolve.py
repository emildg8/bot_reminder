import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def resolve_mention_user_id(
    bot: Bot,
    mention_user_id: int | None,
    mention_username: str | None,
) -> int | None:
    if mention_user_id is not None:
        return mention_user_id
    if not mention_username:
        return None
    try:
        chat = await bot.get_chat(f"@{mention_username.lstrip('@')}")
        return chat.id
    except Exception as exc:
        logger.warning("Cannot resolve @%s: %s", mention_username, exc)
        return None
