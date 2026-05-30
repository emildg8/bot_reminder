from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.repository import async_session, get_active_chat_reminders, get_reminder, is_chat_paused
from bot.handlers.create import _process_text_and_reply
from bot.handlers.edit import _parse_and_confirm_edit
from bot.handlers.diary import _send_journal, _send_stats
from bot.keyboards.inline import examples_keyboard, more_menu_keyboard, timezone_keyboard
from bot.keyboards.reply import (
    BTN_CREATE,
    BTN_DIARY,
    BTN_EXAMPLES,
    BTN_HELP,
    BTN_LIST,
    BTN_MORE,
    BTN_SEARCH,
    BTN_STATS,
    BTN_TIMEZONE,
    MENU_BUTTON_TEXTS,
    main_menu_keyboard,
)
from bot.services.drafts import clear_edit_pending, clear_search_pending, set_search_pending
from bot.services.reminders_ui import send_active_reminders
from bot.services.timezone_ctx import get_effective_timezone, is_group_chat
from bot.texts.messages import CREATE_HINT, EXAMPLES_INTRO, EXAMPLE_PHRASES, HELP_TEXT, format_status, phrase_from_task_preset
from bot.services.pending_tasks import pop_pending_task
from bot.version import __version__

router = Router()


def _clear_modes(user_id: int) -> None:
    clear_edit_pending(user_id)
    clear_search_pending(user_id)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    _clear_modes(message.from_user.id)
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    _clear_modes(message.from_user.id)
    await message.answer("Отменено.", reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    _clear_modes(message.from_user.id)
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
    text = message.text
    if text == BTN_SEARCH:
        clear_edit_pending(message.from_user.id)
        set_search_pending(message.from_user.id)
        await message.answer(
            "🔍 <b>Поиск</b>\n\nНапиши слово или фразу — найду среди активных напоминаний.\n"
            "Отмена: /cancel",
            reply_markup=main_menu_keyboard(),
        )
        return

    _clear_modes(message.from_user.id)
    if text == BTN_LIST:
        await send_active_reminders(message, tab="active")
    elif text == BTN_DIARY:
        await _send_journal(message)
    elif text == BTN_STATS:
        await _send_stats(message)
    elif text == BTN_MORE:
        await message.answer("Дополнительно:", reply_markup=more_menu_keyboard())
    elif text == BTN_CREATE:
        await message.answer(CREATE_HINT, reply_markup=main_menu_keyboard())
    elif text == BTN_TIMEZONE:
        label = "группы" if is_group_chat(message.chat.id) else "личный"
        await message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
    elif text == BTN_HELP:
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
    elif text == BTN_EXAMPLES:
        await message.answer(EXAMPLES_INTRO, reply_markup=examples_keyboard())


@router.callback_query(F.data == "menu:list")
async def menu_list(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await send_active_reminders(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:create")
async def menu_create(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await callback.message.answer(CREATE_HINT)
    await callback.answer()


@router.callback_query(F.data == "menu:more")
async def menu_more(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await callback.message.answer("Дополнительно:", reply_markup=more_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:status")
async def menu_status(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await _send_status(callback.message)
    await callback.answer()


@router.callback_query(F.data == "menu:search")
async def menu_search(callback: CallbackQuery) -> None:
    clear_edit_pending(callback.from_user.id)
    set_search_pending(callback.from_user.id)
    await callback.message.answer(
        "🔍 <b>Поиск</b>\n\nНапиши слово или фразу.\nОтмена: /cancel",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:timezone")
async def menu_timezone(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    label = "группы" if is_group_chat(callback.message.chat.id) else "личный"
    await callback.message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await callback.message.answer(HELP_TEXT)
    await callback.answer()


@router.callback_query(F.data == "menu:examples")
async def menu_examples(callback: CallbackQuery) -> None:
    _clear_modes(callback.from_user.id)
    await callback.message.answer(EXAMPLES_INTRO, reply_markup=examples_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("ex:"))
async def example_picked(callback: CallbackQuery, bot) -> None:
    idx = int(callback.data.split(":", 1)[1])
    if idx < 0 or idx >= len(EXAMPLE_PHRASES):
        await callback.answer("Пример не найден", show_alert=True)
        return
    _, phrase = EXAMPLE_PHRASES[idx]
    _clear_modes(callback.from_user.id)
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
    pending = pop_pending_task(callback.from_user.id)
    if not pending:
        await callback.answer("Задача устарела — отправь текст заново.", show_alert=True)
        return
    phrase = phrase_from_task_preset(pending.text, code)
    await callback.answer()
    if pending.edit_reminder_id is not None:
        async with async_session() as session:
            reminder = await get_reminder(session, pending.edit_reminder_id)
            if reminder is None or not reminder.is_active:
                await callback.message.answer("Напоминание не найдено.")
                return
            timezone = reminder.timezone
        await _parse_and_confirm_edit(
            callback.message,
            pending.edit_reminder_id,
            phrase,
            timezone,
            callback.from_user.id,
            bot,
        )
        return
    await _process_text_and_reply(
        callback.message,
        phrase,
        bot,
        actor_user_id=callback.from_user.id,
        use_phrase_text=True,
    )
