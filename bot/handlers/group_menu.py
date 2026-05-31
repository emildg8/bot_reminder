from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.services.group_menu import show_group_menu_screen
from bot.services.reminders_ui import send_active_reminders

router = Router()


@router.callback_query(F.data == "gmenu:home")
async def gmenu_home(callback: CallbackQuery, bot) -> None:
    await show_group_menu_screen(callback, "home", bot)


@router.callback_query(F.data == "gmenu:hint")
async def gmenu_hint(callback: CallbackQuery, bot) -> None:
    await show_group_menu_screen(callback, "hint", bot)


@router.callback_query(F.data == "gmenu:help")
async def gmenu_help(callback: CallbackQuery, bot) -> None:
    await show_group_menu_screen(callback, "help", bot)


@router.callback_query(F.data == "gmenu:tz")
async def gmenu_tz(callback: CallbackQuery, bot) -> None:
    await show_group_menu_screen(callback, "tz", bot)


@router.callback_query(F.data == "gmenu:examples")
async def gmenu_examples(callback: CallbackQuery, bot) -> None:
    await show_group_menu_screen(callback, "examples", bot)


@router.callback_query(F.data == "gmenu:list")
async def gmenu_list(callback: CallbackQuery) -> None:
    await send_active_reminders(callback.message)
    await callback.answer()
