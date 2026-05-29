from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, update_user_timezone
from bot.keyboards.inline import timezone_keyboard

router = Router()


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
