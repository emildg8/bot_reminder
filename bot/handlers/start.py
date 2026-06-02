from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import (
    async_session,
    complete_user_onboarding,
    get_or_create_chat,
    get_or_create_user,
    update_chat_timezone,
    update_user_timezone,
)
from bot.handlers.create import _process_text_and_reply
from bot.keyboards.inline import main_menu_inline_keyboard, developer_made_by_keyboard, timezone_keyboard, timezone_offset_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.admin_access import is_admin_listed, is_bot_admin
from bot.services.bot_privacy import format_group_privacy_user_hint
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, is_group_chat, tz_scope_label
from bot.services.chat_delivery import format_ops_target_note, resolve_delivery_chat_id
from bot.services.chat_delivery import sync_channel_linked_chat
from bot.services.bot_menu import setup_channel_commands
from bot.services.onboarding import (
    ONBOARDING_TRY_EXAMPLE_INDEX,
    onboarding_keyboard,
    onboarding_step_text,
)
from bot.services.timezone_labels import format_timezone_label
from bot.texts.messages import EXAMPLE_PHRASES, WELCOME_BACK, WELCOME_ONBOARDING, format_collective_welcome, format_developer_made_by_line

router = Router()


def _offset_to_tz(offset_hours: int) -> str:
    if offset_hours == 0:
        return "Etc/UTC"
    sign = "-" if offset_hours > 0 else "+"
    return f"Etc/GMT{sign}{abs(offset_hours)}"


async def _send_onboarding_step(target: Message, step: int) -> None:
    await target.answer(
        onboarding_step_text(step),
        reply_markup=onboarding_keyboard(step),
    )


async def _finish_onboarding(callback: CallbackQuery) -> None:
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id, settings.default_timezone
        )
        await complete_user_onboarding(session, user)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "⌨️ Меню:",
        reply_markup=menu_keyboard_for_chat(
            callback.message.chat.id, callback.from_user.id
        ),
    )
    await callback.message.answer("⚡️ Быстрые действия:", reply_markup=main_menu_inline_keyboard())
    await callback.message.answer(
        format_developer_made_by_line(),
        reply_markup=developer_made_by_keyboard(),
    )


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
            ops_id = await resolve_delivery_chat_id(
                session, message.chat.id, message.chat.type
            )
            chat = await get_or_create_chat(session, ops_id, settings.default_timezone)
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
        privacy_hint = format_group_privacy_user_hint(
            can_read_all_group_messages=me.can_read_all_group_messages,
        )
        await message.answer(format_collective_welcome(kind, me.username, privacy_hint=privacy_hint))
        return

    await message.answer(
        WELCOME_BACK.format(
            tz_scope=tz_scope_label(kind),
            tz_label=format_timezone_label(tz),
        ),
        reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
    )

    if is_admin_listed(message.from_user.id):
        from bot.texts.messages import format_admin_help_footer

        await message.answer(
            format_admin_help_footer(admin_tools=is_bot_admin(message.from_user.id))
        )

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, settings.default_timezone)
        needs_tour = not user.onboarding_done

    if needs_tour:
        await _send_onboarding_step(message, 1)
        return

    await message.answer("⚡️ Быстрые действия:", reply_markup=main_menu_inline_keyboard())


@router.message(lambda m: m.text and m.text.startswith("/timezone"))
async def cmd_timezone(message: Message) -> None:
    kind = chat_kind_from_chat(message.chat)
    scope = "личный" if kind == ChatKind.PRIVATE else tz_scope_label(kind)
    await message.answer(f"🕐 Выбери часовой пояс ({scope}):", reply_markup=timezone_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("onb:"))
async def onboarding_callback(callback: CallbackQuery, bot) -> None:
    if callback.message.chat.id <= 0:
        await callback.answer()
        return

    action = callback.data.split(":", 1)[1]

    if action == "restart":
        await callback.answer()
        await _send_onboarding_step(callback.message, 1)
        return

    if action == "skip" or action == "done":
        await callback.answer()
        await _finish_onboarding(callback)
        return

    if action == "try":
        await callback.answer()
        async with async_session() as session:
            user = await get_or_create_user(
                session, callback.from_user.id, settings.default_timezone
            )
            await complete_user_onboarding(session, user)
        await callback.message.edit_reply_markup(reply_markup=None)
        _, phrase = EXAMPLE_PHRASES[ONBOARDING_TRY_EXAMPLE_INDEX]
        await _process_text_and_reply(
            callback.message,
            phrase,
            bot,
            actor_user_id=callback.from_user.id,
        )
        return

    if action.startswith("next:"):
        step = int(action.split(":", 1)[1])
        await callback.answer()
        await callback.message.edit_text(
            onboarding_step_text(step),
            reply_markup=onboarding_keyboard(step),
        )
        return

    await callback.answer()


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
            ops_id = await resolve_delivery_chat_id(
                session, chat_id, callback.message.chat.type
            )
            chat = await get_or_create_chat(session, ops_id, settings.default_timezone)
            await update_chat_timezone(session, chat, timezone)
            scope = tz_scope_label(kind)
            label = f"✅ Часовой пояс {scope}: <b>{tz_label}</b>"
            label += format_ops_target_note(chat_id, ops_id)
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
            await _send_onboarding_step(callback.message, 1)
    await callback.answer("Сохранено")


@router.callback_query(lambda c: c.data and c.data.startswith("tz_off:"))
async def set_timezone_offset(callback: CallbackQuery) -> None:
    offset = int(callback.data.split(":", 1)[1])
    await _apply_timezone(callback, _offset_to_tz(offset))


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def set_timezone(callback: CallbackQuery) -> None:
    timezone = callback.data.split(":", 1)[1]
    await _apply_timezone(callback, timezone)
