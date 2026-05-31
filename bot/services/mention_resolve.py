import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus

logger = logging.getLogger(__name__)

_INACTIVE = frozenset(
    {
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    }
)


async def is_user_in_chat(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status not in _INACTIVE
    except Exception as exc:
        logger.warning("Cannot check member %s in chat %s: %s", user_id, chat_id, exc)
        return False


async def resolve_mention_user_id(
    bot: Bot,
    mention_user_id: int | None,
    mention_username: str | None,
    *,
    chat_id: int | None = None,
) -> int | None:
    user_id = mention_user_id
    if user_id is None and mention_username:
        try:
            chat = await bot.get_chat(f"@{mention_username.lstrip('@')}")
            user_id = chat.id
        except Exception as exc:
            logger.warning("Cannot resolve @%s: %s", mention_username, exc)
            return None

    if user_id is None:
        return None

    if chat_id is not None and chat_id < 0:
        if not await is_user_in_chat(bot, chat_id, user_id):
            logger.info("User %s is not in chat %s", user_id, chat_id)
            return None

    return user_id
