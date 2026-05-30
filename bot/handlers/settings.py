from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, update_user_snooze_settings
from bot.keyboards.inline import settings_snooze_keyboard
from bot.services.user_prefs import get_snooze_presets, get_snooze_step, parse_snooze_presets

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, settings.default_timezone)
        presets = get_snooze_presets(user)
        step = get_snooze_step(user)
    await message.answer(
        "⚙️ <b>Настройки отложить</b>\n\n"
        "Stepper «⏰ Отложить»: шаг +/− и быстрые пресеты.\n"
        "Выбери профиль или шаг:",
        reply_markup=settings_snooze_keyboard(presets, step),
    )


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery) -> None:
    await cmd_settings(callback.message)
    await callback.answer()


@router.callback_query(F.data == "set:pre:std")
async def set_presets_std(callback: CallbackQuery) -> None:
    await _apply_presets(callback, "5,15,30,60")


@router.callback_query(F.data == "set:pre:long")
async def set_presets_long(callback: CallbackQuery) -> None:
    await _apply_presets(callback, "5,15,30,60,180,240")


@router.callback_query(F.data == "set:step")
async def cycle_step(callback: CallbackQuery) -> None:
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, settings.default_timezone)
        current = get_snooze_step(user)
        options = [5, 15, 30, 60]
        try:
            idx = options.index(current)
            new_step = options[(idx + 1) % len(options)]
        except ValueError:
            new_step = 15
        await update_user_snooze_settings(session, user, step=new_step)
        presets = get_snooze_presets(user)
    await callback.message.edit_reply_markup(
        reply_markup=settings_snooze_keyboard(presets, new_step),
    )
    await callback.answer(f"Шаг: {new_step} мин")


async def _apply_presets(callback: CallbackQuery, raw: str) -> None:
    presets = parse_snooze_presets(raw)
    async with async_session() as session:
        user = await get_or_create_user(session, callback.from_user.id, settings.default_timezone)
        await update_user_snooze_settings(session, user, presets=raw)
        step = get_snooze_step(user)
    await callback.message.edit_reply_markup(
        reply_markup=settings_snooze_keyboard(presets, step),
    )
    await callback.answer("Пресеты обновлены")
