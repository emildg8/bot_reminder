from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.repository import async_session, get_active_chat_reminders, is_chat_paused
from bot.handlers.create import _process_text_and_reply
from bot.keyboards.inline import examples_keyboard, timezone_keyboard
from bot.keyboards.reply import (
    BTN_CREATE,
    BTN_EXAMPLES,
    BTN_HELP,
    BTN_LIST,
    BTN_STATUS,
    BTN_TIMEZONE,
    MENU_BUTTON_TEXTS,
    main_menu_keyboard,
)
from bot.services.drafts import clear_edit_pending
from bot.services.reminders_ui import send_active_reminders
from bot.services.timezone_ctx import get_effective_timezone, is_group_chat
from bot.texts.messages import CREATE_HINT, EXAMPLES_INTRO, EXAMPLE_PHRASES, HELP_TEXT, format_status, phrase_from_task_preset
from bot.services.pending_tasks import get_pending_task, pop_pending_task
from bot.version import __version__

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    clear_edit_pending(message.from_user.id)
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    clear_edit_pending(message.from_user.id)
    await message.answer(
        "⌨️ <b>Меню</b> — кнопки внизу или команды через /",
        reply_markup=main_menu_keyboard(),
    )


async def _send_status(message: Message) -> None:
    chat_id = message.chat.id
    async with async_session() as session:
        count = len(await get_active_chat_reminders(session, chat_id))
        paused = await is_chat_paused(session, chat_id)
        tz = await get_effective_timezone(session, chat_id, message.from_user.id)

    tz_scope = "группы" if is_group_chat(chat_id) else "твой"
    await message.answer(
        format_status(count=count, paused=paused, tz=tz, tz_scope=tz_scope, version=__version__),
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text.in_(MENU_BUTTON_TEXTS))
async def handle_menu_buttons(message: Message, bot) -> None:
    clear_edit_pending(message.from_user.id)
    text = message.text
    if text == BTN_LIST:
        await send_active_reminders(message)
    elif text == BTN_CREATE:
        await message.answer(CREATE_HINT, reply_markup=main_menu_keyboard())
    elif text == BTN_STATUS:
        await _send_status(message)
    elif text == BTN_TIMEZONE:
        label = "группы" if is_group_chat(message.chat.id) else "личный"
        await message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
    elif text == BTN_HELP:
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
    elif text == BTN_EXAMPLES:
        await message.answer(EXAMPLES_INTRO, reply_markup=examples_keyboard())


@router.callback_query(F.data == "menu:list")
async def menu_list(callback: CallbackQuery) -> None:
    await send_active_reminders(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:create")
async def menu_create(callback: CallbackQuery) -> None:
    await callback.message.answer(CREATE_HINT)
    await callback.answer()


@router.callback_query(F.data == "menu:status")
async def menu_status(callback: CallbackQuery) -> None:
    await _send_status(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:timezone")
async def menu_timezone(callback: CallbackQuery) -> None:
    label = "группы" if is_group_chat(callback.message.chat.id) else "личный"
    await callback.message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.answer(HELP_TEXT)
    await callback.answer()


@router.callback_query(F.data == "menu:examples")
async def menu_examples(callback: CallbackQuery) -> None:
    await callback.message.answer(EXAMPLES_INTRO, reply_markup=examples_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("ex:"))
async def example_picked(callback: CallbackQuery, bot) -> None:
    idx = int(callback.data.split(":", 1)[1])
    if idx < 0 or idx >= len(EXAMPLE_PHRASES):
        await callback.answer("Пример не найден", show_alert=True)
        return
    _, phrase = EXAMPLE_PHRASES[idx]
    await callback.answer()
    await _process_text_and_reply(
        callback.message,
        phrase,
        bot,
        actor_user_id=callback.from_user.id,
        use_phrase_text=True,
    )


@router.callback_query(F.data.startswith("qt:"))
async def task_time_picked(callback: CallbackQuery, bot) -> None:
    code = callback.data.split(":", 1)[1]
    task = get_pending_task(callback.from_user.id)
    if not task:
        await callback.answer("Задача устарела — отправь текст заново.", show_alert=True)
        return
    pop_pending_task(callback.from_user.id)
    phrase = phrase_from_task_preset(task, code)
    await callback.answer()
    await _process_text_and_reply(
        callback.message,
        phrase,
        bot,
        actor_user_id=callback.from_user.id,
        use_phrase_text=True,
    )
