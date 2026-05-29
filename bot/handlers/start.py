from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, update_user_timezone
from bot.keyboards.inline import main_menu_inline_keyboard, timezone_keyboard, timezone_offset_keyboard
from bot.keyboards.reply import main_menu_keyboard

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

    await message.answer(
        "Привет! Я бот-напоминалка.\n\n"
        "Создай напоминание текстом, голосом или кружочком.\n"
        "Или выбери действие кнопками ниже.\n\n"
        f"Часовой пояс: <b>{user.timezone}</b>",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(
        "Быстрые действия:",
        reply_markup=main_menu_inline_keyboard(),
    )


@router.message(lambda m: m.text and m.text.startswith("/timezone"))
async def cmd_timezone(message: Message) -> None:
    await message.answer("Выбери часовой пояс:", reply_markup=timezone_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("tz_menu:"))
async def tz_menu(callback: CallbackQuery) -> None:
    target = callback.data.split(":", 1)[1]
    if target == "offset":
        await callback.message.edit_text("Выбери UTC offset:", reply_markup=timezone_offset_keyboard())
    else:
        await callback.message.edit_text("Выбери часовой пояс:", reply_markup=timezone_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("tz_off:"))
async def set_timezone_offset(callback: CallbackQuery) -> None:
    offset = int(callback.data.split(":", 1)[1])
    timezone = _offset_to_tz(offset)
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone=settings.default_timezone,
        )
        await update_user_timezone(session, user, timezone)

    await callback.message.edit_text(f"Часовой пояс установлен: {timezone}")
    await callback.answer("Сохранено")


@router.callback_query(lambda c: c.data and c.data.startswith("tz:"))
async def set_timezone(callback: CallbackQuery) -> None:
    timezone = callback.data.split(":", 1)[1]
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            timezone=settings.default_timezone,
        )
        await update_user_timezone(session, user, timezone)

    await callback.message.edit_text(f"Часовой пояс установлен: {timezone}")
    await callback.answer("Сохранено")
