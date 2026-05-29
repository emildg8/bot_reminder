from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import main_menu_inline_keyboard, timezone_keyboard
from bot.keyboards.reply import (
    BTN_CREATE,
    BTN_EXAMPLES,
    BTN_HELP,
    BTN_LIST,
    BTN_TIMEZONE,
    MENU_BUTTON_TEXTS,
    main_menu_keyboard,
)
from bot.services.reminders_ui import send_active_reminders
from bot.texts.help import CREATE_HINT, EXAMPLES_TEXT, HELP_TEXT

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await message.answer(
        "Главное меню — выбери действие кнопкой ниже или в меню команд (/)",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text.in_(MENU_BUTTON_TEXTS))
async def handle_menu_buttons(message: Message) -> None:
    text = message.text
    if text == BTN_LIST:
        await send_active_reminders(message)
    elif text == BTN_CREATE:
        await message.answer(CREATE_HINT, reply_markup=main_menu_keyboard())
    elif text == BTN_TIMEZONE:
        await message.answer("Выбери часовой пояс:", reply_markup=timezone_keyboard())
    elif text == BTN_HELP:
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
    elif text == BTN_EXAMPLES:
        await message.answer(EXAMPLES_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:list")
async def menu_list(callback: CallbackQuery) -> None:
    await send_active_reminders(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:create")
async def menu_create(callback: CallbackQuery) -> None:
    await callback.message.answer(CREATE_HINT)
    await callback.answer()


@router.callback_query(F.data == "menu:timezone")
async def menu_timezone(callback: CallbackQuery) -> None:
    await callback.message.answer("Выбери часовой пояс:", reply_markup=timezone_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.answer(HELP_TEXT)
    await callback.answer()


@router.callback_query(F.data == "menu:examples")
async def menu_examples(callback: CallbackQuery) -> None:
    await callback.message.answer(EXAMPLES_TEXT)
    await callback.answer()
