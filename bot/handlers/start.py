from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import (
    async_session,
    get_or_create_chat,
    get_or_create_user,
    update_chat_timezone,
    update_user_timezone,
)
from bot.keyboards.inline import main_menu_inline_keyboard, timezone_keyboard, timezone_offset_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, is_group_chat, tz_scope_label
from bot.services.chat_delivery import sync_channel_linked_chat
from bot.services.bot_menu import setup_channel_commands
from bot.services.timezone_labels import format_timezone_label
from bot.texts.messages import (
    ONBOARDING_READY,
    WELCOME_BACK,
    WELCOME_ONBOARDING,
    format_collective_welcome,
)

router = Router()


def _offset_to_tz(offset_hours: int) -> str:
    if offset_hours == 0:
        return "Etc/UTC"
    sign = "-" if offset_hours > 0 else "+"
    return f"Etc/GMT{sign}{abs(offset_hours)}"


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            timezone=settings.default_timezone,
        )

    if not user.timezone_confirmed and message.chat.id > 0:
        await message.answer(WELCOME_ONBOARDING, reply_markup=timezone_keyboard())
        return

    kind = chat_kind_from_chat(message.chat)
    async with async_session() as session:
        if is_group_chat(message.chat.id):
            chat = await get_or_create_chat(session, message.chat.id, settings.default_timezone)
            tz = chat.timezone
        else:
            tz = user.timezone

    if kind != ChatKind.PRIVATE:
        me = await message.bot.get_me()
        if kind == ChatKind.CHANNEL:
            async with async_session() as session:
                await sync_channel_linked_chat(
                    message.bot,
                    session,
                    message.chat.id,
                    default_timezone=settings.default_timezone,
                )
            await setup_channel_commands(message.bot, message.chat.id)
        await message.answer(format_collective_welcome(kind, me.username))
        if kind != ChatKind.CHANNEL:
            await message.answer(
                "⚡️ Быстрые действия:",
                reply_markup=main_menu_inline_keyboard(),
            )
        return

    await message.answer(
        WELCOME_BACK.format(
            tz_scope=tz_scope_label(kind),
            tz_label=format_timezone_label(tz),
        ),
        reply_markup=menu_keyboard_for_chat(message.chat.id),
    )
    await message.answer("⚡️ Быстрые действия:", reply_markup=main_menu_inline_keyboard())


@router.message(lambda m: m.text and m.text.startswith("/timezone"))
async def cmd_timezone(message: Message) -> None:
    kind = chat_kind_from_chat(message.chat)
    scope = "личный" if kind == ChatKind.PRIVATE else tz_scope_label(kind)
    await message.answer(f"🕐 Выбери часовой пояс ({scope}):", reply_markup=timezone_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("tz_menu:"))
async def tz_menu(callback: CallbackQuery) -> None:
    target = callback.data.split(":", 1)[1]
    if target == "offset":
        await callback.message.edit_text("🕐 Выбери смещение от UTC:", reply_markup=timezone_offset_keyboard())
    else:
        await callback.message.edit_text("🕐 Выбери часовой пояс:", reply_markup=timezone_keyboard())
    await callback.answer()


async def _apply_timezone(callback: CallbackQuery, timezone: str) -> None:
    from bot.services.chat_permissions import can_manage_group_reminders

    chat_id = callback.message.chat.id
    kind = chat_kind_from_chat(callback.message.chat)
    if is_group_chat(chat_id):
        if not await can_manage_group_reminders(callback.bot, chat_id, callback.from_user.id):
            scope = "канала" if kind == ChatKind.CHANNEL else "группы"
            await callback.answer(
                f"Только администраторы могут менять часовой пояс {scope}.",
                show_alert=True,
            )
            return

    tz_label = format_timezone_label(timezone)
    was_first_setup = False
    async with async_session() as session:
        if is_group_chat(chat_id):
            chat = await get_or_create_chat(session, chat_id, settings.default_timezone)
            await update_chat_timezone(session, chat, timezone)
            scope = tz_scope_label(kind)
            label = f"✅ Часовой пояс {scope}: <b>{tz_label}</b>"
        else:
            user = await get_or_create_user(
                session, callback.from_user.id, settings.default_timezone
            )
            was_first_setup = not user.timezone_confirmed
            await update_user_timezone(session, user, timezone)
            label = f"✅ Часовой пояс: <b>{tz_label}</b>"

    await callback.message.edit_text(label + "\n\nМожешь создавать напоминания ✨")
    if not is_group_chat(chat_id):
        await callback.message.answer("⌨️ Меню:", reply_markup=menu_keyboard_for_chat(chat_id))
        if was_first_setup:
            await callback.message.answer(ONBOARDING_READY, reply_markup=main_menu_inline_keyboard())
    await callback.answer("Сохранено")


@router.callback_query(lambda c: c.data and c.data.startswith("tz_off:"))
async def set_timezone_offset(callback: CallbackQuery) -> None:
    offset = int(callback.data.split(":", 1)[1])
    await _apply_timezone(callback, _offset_to_tz(offset))


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def set_timezone(callback: CallbackQuery) -> None:
    timezone = callback.data.split(":", 1)[1]
    await _apply_timezone(callback, timezone)
