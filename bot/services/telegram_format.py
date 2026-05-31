"""HTML-текст напоминания с опциональным упоминанием."""

from html import escape

from aiogram.enums import ChatType

from bot.services.chat_ctx import ChatKind, chat_kind_from_type, is_group_chat


def format_reminder_message(
    text: str,
    *,
    mention_user_id: int | None = None,
    mention_username: str | None = None,
    creator_user_id: int | None = None,
    creator_username: str | None = None,
    chat_id: int,
    chat_type: str | ChatType | None = None,
    chat_title: str | None = None,
) -> str:
    kind = chat_kind_from_type(chat_type)
    if kind == ChatKind.CHANNEL:
        title = escape(chat_title) if chat_title else "Канал"
        return f"📢 <b>{title}</b>\n⏰ <b>{escape(text)}</b>"

    prefix = ""
    target_id = mention_user_id
    target_username = mention_username

    if target_id is None and is_group_chat(chat_id):
        target_id = creator_user_id
        target_username = creator_username

    if target_id is not None:
        if target_username:
            prefix = f'<a href="tg://user?id={target_id}">@{escape(target_username)}</a>, '
        else:
            prefix = f'<a href="tg://user?id={target_id}">участник</a>, '

    return f"⏰ {prefix}<b>{escape(text)}</b>"
