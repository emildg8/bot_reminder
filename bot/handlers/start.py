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
from bot.keyboards.reply import main_menu_keyboard
from bot.services.timezone_ctx import is_group_chat

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
        await message.answer(
            "Привет! Я бот-напоминалка.\n\n"
            "Сначала выбери часовой пояс — от него зависит время напоминаний:",
            reply_markup=timezone_keyboard(),
        )
        return

    tz_label = "группы" if is_group_chat(message.chat.id) else "твой"
    async with async_session() as session:
        if is_group_chat(message.chat.id):
            chat = await get_or_create_chat(session, message.chat.id, settings.default_timezone)
            tz = chat.timezone
        else:
            tz = user.timezone

    await message.answer(
        "Привет! Я бот-напоминалка.\n\n"
        "Создай напоминание текстом, голосом или кружочком.\n"
        "Или выбери действие кнопками ниже.\n\n"
        f"Часовой пояс ({tz_label}): <b>{tz}</b>",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer("Быстрые действия:", reply_markup=main_menu_inline_keyboard())


@router.message(lambda m: m.text and m.text.startswith("/timezone"))
async def cmd_timezone(message: Message) -> None:
    label = "группы" if is_group_chat(message.chat.id) else "личный"
    await message.answer(f"Выбери часовой пояс ({label}):", reply_markup=timezone_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("tz_menu:"))
async def tz_menu(callback: CallbackQuery) -> None:
    target = callback.data.split(":", 1)[1]
    if target == "offset":
        await callback.message.edit_text("Выбери UTC offset:", reply_markup=timezone_offset_keyboard())
    else:
        await callback.message.edit_text("Выбери часовой пояс:", reply_markup=timezone_keyboard())
    await callback.answer()


async def _apply_timezone(callback: CallbackQuery, timezone: str) -> None:
    chat_id = callback.message.chat.id
    async with async_session() as session:
        if is_group_chat(chat_id):
            chat = await get_or_create_chat(session, chat_id, settings.default_timezone)
            await update_chat_timezone(session, chat, timezone)
            label = f"Часовой пояс группы: {timezone}"
        else:
            user = await get_or_create_user(
                session, callback.from_user.id, settings.default_timezone
            )
            await update_user_timezone(session, user, timezone)
            label = f"Часовой пояс: {timezone}"

    await callback.message.edit_text(label + "\n\nМожешь создавать напоминания!")
    if not is_group_chat(chat_id):
        await callback.message.answer("Меню:", reply_markup=main_menu_keyboard())
    await callback.answer("Сохранено")


@router.callback_query(lambda c: c.data and c.data.startswith("tz_off:"))
async def set_timezone_offset(callback: CallbackQuery) -> None:
    offset = int(callback.data.split(":", 1)[1])
    await _apply_timezone(callback, _offset_to_tz(offset))


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def set_timezone(callback: CallbackQuery) -> None:
    timezone = callback.data.split(":", 1)[1]
    await _apply_timezone(callback, timezone)
