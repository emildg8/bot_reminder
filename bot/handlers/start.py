from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, update_user_timezone
from bot.keyboards.inline import timezone_keyboard, timezone_offset_keyboard

router = Router()

def _offset_to_tz(offset_hours: int) -> str:
    # zoneinfo uses inverted sign in Etc/GMT zones:
    # UTC+3 == Etc/GMT-3
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
        "Напиши, скажи голосом или отправь кружочек, например:\n"
        "• через час выпить таблетки\n"
        "• каждые 30 минут встать\n"
        "• каждый день в 9:00 зарядка\n\n"
        f"Твоя timezone: {user.timezone}\n"
        "Можешь изменить её кнопками ниже или командой /timezone",
        reply_markup=timezone_keyboard(),
    )


@router.message(lambda m: m.text and m.text.startswith("/timezone"))
async def cmd_timezone(message: Message) -> None:
    await message.answer("Выбери timezone:", reply_markup=timezone_keyboard())

@router.callback_query(lambda c: c.data and c.data.startswith("tz_menu:"))
async def tz_menu(callback: CallbackQuery) -> None:
    target = callback.data.split(":", 1)[1]
    if target == "offset":
        await callback.message.edit_text("Выбери UTC offset:", reply_markup=timezone_offset_keyboard())
    else:
        await callback.message.edit_text("Выбери timezone:", reply_markup=timezone_keyboard())
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

    await callback.message.edit_text(f"Timezone установлена: {timezone}")
    await callback.answer()


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

    await callback.message.edit_text(f"Timezone установлена: {timezone}")
    await callback.answer()
