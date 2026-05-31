"""Тип чата: личка, группа, канал — для текстов и UX."""

from __future__ import annotations

from enum import Enum

from aiogram.enums import ChatType
from aiogram.types import Chat


class ChatKind(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


def chat_kind_from_type(chat_type: str | ChatType | None) -> ChatKind:
    if chat_type is None:
        return ChatKind.SUPERGROUP
    value = chat_type.value if isinstance(chat_type, ChatType) else str(chat_type)
    if value == ChatType.PRIVATE.value:
        return ChatKind.PRIVATE
    if value == ChatType.CHANNEL.value:
        return ChatKind.CHANNEL
    if value == ChatType.GROUP.value:
        return ChatKind.GROUP
    return ChatKind.SUPERGROUP


def chat_kind_from_chat(chat: Chat) -> ChatKind:
    return chat_kind_from_type(chat.type)


def chat_kind_from_id(chat_id: int, chat_type: str | ChatType | None = None) -> ChatKind:
    if chat_id > 0:
        return ChatKind.PRIVATE
    if chat_type is not None:
        return chat_kind_from_type(chat_type)
    return ChatKind.SUPERGROUP


def is_private_chat(chat_id: int) -> bool:
    return chat_id > 0


def is_collective_chat(chat_id: int, chat_type: str | ChatType | None = None) -> bool:
    return chat_kind_from_id(chat_id, chat_type) != ChatKind.PRIVATE


def is_group_chat(chat_id: int) -> bool:
    """Обратная совместимость: любой не-личный чат (группа, супергруппа, канал)."""
    return chat_id < 0


def is_group_like(chat_type: str | ChatType | None) -> bool:
    kind = chat_kind_from_type(chat_type)
    return kind in (ChatKind.GROUP, ChatKind.SUPERGROUP)


def is_channel(chat_type: str | ChatType | None) -> bool:
    return chat_kind_from_type(chat_type) == ChatKind.CHANNEL


def collective_place_label(chat_kind: ChatKind) -> str:
    if chat_kind == ChatKind.CHANNEL:
        return "канале"
    return "группе"


def collective_noun(chat_kind: ChatKind) -> str:
    if chat_kind == ChatKind.CHANNEL:
        return "канал"
    return "группа"


def tz_scope_label(chat_kind: ChatKind) -> str:
    if chat_kind == ChatKind.PRIVATE:
        return "твой"
    if chat_kind == ChatKind.CHANNEL:
        return "канала"
    return "группы"
