import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.repository import async_session, get_reminder
from bot.handlers.create import _process_text_and_reply
from bot.handlers.edit import _parse_and_confirm_edit
from bot.handlers.diary import _send_journal, _send_stats
from bot.keyboards.inline import (
    examples_keyboard,
    main_menu_inline_keyboard,
    more_menu_keyboard,
    timezone_keyboard,
)
from bot.services.callback_utils import safe_callback_answer
from bot.services.group_menu import (
    is_group_menu_chat,
    send_group_commands_hint,
)
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
    menu_keyboard_for_chat,
)
from bot.services.drafts import clear_edit_pending, clear_search_pending, set_search_pending
from bot.services.reminders_ui import send_active_reminders
from bot.services.chat_ctx import chat_kind_from_chat, tz_scope_label
from bot.services.chat_status import build_status_text
from bot.services.create_confirm import deliver_create_confirm
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.pending_assignee import clear_pending_assignee, pop_pending_assignee
from bot.services.pending_tasks import clear_pending_task, pop_pending_task
from bot.services.nlp.ambiguous_time import phrase_from_ambiguous_choice, phrase_from_day_only_choice
from bot.services.help_display import format_help_for_chat, format_help_for_message
from bot.texts.messages import (
    CREATE_HINT,
    EXAMPLES_INTRO,
    EXAMPLE_PHRASES,
    phrase_from_task_preset,
)
from bot.handlers.tips import send_thanks_screen
from bot.services.tip_custom_state import clear_all_tip_custom, is_pending_confirm, is_waiting_custom_amount
from bot.version import __version__

logger = logging.getLogger(__name__)

router = Router()


def _clear_modes(user_id: int) -> None:
    clear_edit_pending(user_id)
    clear_search_pending(user_id)
    clear_pending_task(user_id)
    clear_pending_assignee(user_id)
    clear_all_tip_custom(user_id)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    _clear_modes(message.from_user.id)
    await message.answer(format_help_for_message(message), reply_markup=menu_keyboard_for_chat(message.chat.id))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    user_id = message.from_user.id
    was_tip = is_waiting_custom_amount(user_id) or is_pending_confirm(user_id)
    _clear_modes(user_id)
    text = "Режим Stars отменён." if was_tip else "Отменено."
    await message.answer(
        text,
        reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, bot) -> None:
    _clear_modes(message.from_user.id)
    if is_group_menu_chat(message.chat):
        await send_group_commands_hint(message, bot)
        return
    await message.answer(
        "⌨️ <b>Меню</b> — кнопки внизу или команды через /",
        reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
    )


async def _send_status(message: Message, bot) -> None:
    text = await build_status_text(bot, message)
    await message.answer(
        text,
        reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
    )


@router.message(F.text.in_(MENU_BUTTON_TEXTS))
async def handle_menu_buttons(message: Message, bot) -> None:
    if is_group_menu_chat(message.chat):
        return

    text = message.text
    if text == BTN_SEARCH:
        clear_edit_pending(message.from_user.id)
        clear_pending_task(message.from_user.id)
        clear_all_tip_custom(message.from_user.id)
        set_search_pending(message.from_user.id)
        await message.answer(
            "🔍 <b>Поиск</b>\n\nНапиши слово или фразу — найду среди активных напоминаний.\n"
            "Отмена: /cancel",
            reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
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
        await message.answer(
            "Дополнительно:",
            reply_markup=more_menu_keyboard(message.from_user.id),
        )
    elif text == BTN_CREATE:
        await message.answer(
            CREATE_HINT,
            reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
        )
    elif text == BTN_TIMEZONE:
        label = tz_scope_label(chat_kind_from_chat(message.chat))
        await message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
    elif text == BTN_HELP:
        await message.answer(
            format_help_for_message(message),
            reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
        )
    elif text == BTN_EXAMPLES:
        await message.answer(EXAMPLES_INTRO, reply_markup=examples_keyboard())


@router.callback_query(F.data == "menu:list")
async def menu_list(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)
    _clear_modes(callback.from_user.id)
    await send_active_reminders(callback.message)


@router.callback_query(F.data == "menu:home")
async def menu_home(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)
    _clear_modes(callback.from_user.id)
    await callback.message.edit_text(
        "⌨️ <b>Меню</b>",
        reply_markup=main_menu_inline_keyboard(),
    )


@router.callback_query(F.data == "menu:create")
async def menu_create(callback: CallbackQuery, bot) -> None:
    _clear_modes(callback.from_user.id)
    if is_group_menu_chat(callback.message.chat):
        await safe_callback_answer(callback)
        me = await bot.get_me()
        uname = me.username or "бот"
        await callback.message.answer(
            f"✍️ <code>/remind@{uname} через 30 минут …</code>",
        )
        return
    await safe_callback_answer(callback)
    await callback.message.answer(CREATE_HINT)


@router.callback_query(F.data == "menu:thanks")
async def menu_thanks(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)
    _clear_modes(callback.from_user.id)
    await send_thanks_screen(callback.message)


@router.callback_query(F.data == "menu:more")
async def menu_more(callback: CallbackQuery, bot) -> None:
    _clear_modes(callback.from_user.id)
    if is_group_menu_chat(callback.message.chat):
        await safe_callback_answer(callback)
        await callback.message.answer(
            format_help_for_chat(callback.message.chat, callback.from_user.id)
        )
        return
    await safe_callback_answer(callback)
    await callback.message.edit_text(
        "Дополнительно:",
        reply_markup=more_menu_keyboard(callback.from_user.id),
    )


@router.callback_query(F.data == "menu:status")
async def menu_status(callback: CallbackQuery, bot) -> None:
    await safe_callback_answer(callback)
    _clear_modes(callback.from_user.id)
    await _send_status(callback.message, bot)


@router.callback_query(F.data == "menu:search")
async def menu_search(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)
    clear_edit_pending(callback.from_user.id)
    clear_pending_task(callback.from_user.id)
    set_search_pending(callback.from_user.id)
    await callback.message.answer(
        "🔍 <b>Поиск</b>\n\nНапиши слово или фразу.\nОтмена: /cancel",
        reply_markup=menu_keyboard_for_chat(callback.message.chat.id),
    )


@router.callback_query(F.data == "menu:timezone")
async def menu_timezone(callback: CallbackQuery, bot) -> None:
    _clear_modes(callback.from_user.id)
    if is_group_menu_chat(callback.message.chat):
        await safe_callback_answer(callback)
        label = tz_scope_label(chat_kind_from_chat(callback.message.chat))
        await callback.message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())
        return
    await safe_callback_answer(callback)
    label = tz_scope_label(chat_kind_from_chat(callback.message.chat))
    await callback.message.answer(f"🕐 Часовой пояс ({label}):", reply_markup=timezone_keyboard())


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery, bot) -> None:
    _clear_modes(callback.from_user.id)
    if is_group_menu_chat(callback.message.chat):
        await safe_callback_answer(callback)
        await callback.message.answer(
            format_help_for_chat(callback.message.chat, callback.from_user.id)
        )
        return
    await safe_callback_answer(callback)
    await callback.message.answer(
        format_help_for_chat(callback.message.chat, callback.from_user.id)
    )


@router.callback_query(F.data == "menu:about")
async def menu_about(callback: CallbackQuery) -> None:
    from bot.texts.messages import format_about

    await safe_callback_answer(callback)
    _clear_modes(callback.from_user.id)
    await callback.message.answer(format_about(__version__))


@router.callback_query(F.data == "menu:examples")
async def menu_examples(callback: CallbackQuery, bot) -> None:
    _clear_modes(callback.from_user.id)
    if is_group_menu_chat(callback.message.chat):
        await safe_callback_answer(callback)
        me = await bot.get_me()
        uname = me.username or "бот"
        await callback.message.answer(
            f"💡 Примеры: <code>/remind@{uname} через час созвон</code>",
        )
        return
    await safe_callback_answer(callback)
    await callback.message.edit_text(EXAMPLES_INTRO, reply_markup=examples_keyboard(back_callback="menu:home"))


@router.callback_query(F.data.startswith("ex:"))
async def example_picked(callback: CallbackQuery, bot) -> None:
    idx = int(callback.data.split(":", 1)[1])
    if idx < 0 or idx >= len(EXAMPLE_PHRASES):
        await safe_callback_answer(callback, "Пример не найден", show_alert=True)
        return
    _, phrase = EXAMPLE_PHRASES[idx]
    _clear_modes(callback.from_user.id)
    await safe_callback_answer(callback)
    try:
        await _process_text_and_reply(
            callback.message,
            phrase,
            bot,
            actor_user_id=callback.from_user.id,
        )
    except Exception:
        logger.exception("Example callback failed idx=%s chat=%s", idx, callback.message.chat.id)
        await callback.message.answer(
            "⚠️ Не удалось создать из примера. Попробуй /remind или напиши фразу заново."
        )


@router.callback_query(F.data.startswith("qt:"))
async def task_time_picked(callback: CallbackQuery, bot) -> None:
    code = callback.data.split(":", 1)[1]
    pending = pop_pending_task(callback.from_user.id)
    if not pending:
        await callback.answer("Задача устарела — отправь текст заново.", show_alert=True)
        return
    phrase = phrase_from_task_preset(pending.text, code)
    await safe_callback_answer(callback)
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
    )


@router.callback_query(F.data.startswith("as:"))
async def assignee_selected(callback: CallbackQuery, bot: Bot) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "_cancel":
        clear_pending_assignee(callback.from_user.id)
        await safe_callback_answer(callback, "Отменено")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    pending = pop_pending_assignee(callback.from_user.id)
    if not pending:
        await safe_callback_answer(callback, "Выбор устарел — напиши фразу заново.", show_alert=True)
        return

    if key == "_none":
        mention_username = None
        mention_source = None
        mention_provided = False
        mention_pick_note = None
    else:
        try:
            idx = int(key)
            mention_username = pending.candidates[idx]
        except (ValueError, IndexError):
            await safe_callback_answer(callback, "Некорректный выбор.", show_alert=True)
            return
        mention_source = "text"
        mention_provided = True
        mention_pick_note = None

    mention_telegram_id = await resolve_mention_user_id(
        bot,
        None,
        mention_username,
        chat_id=callback.message.chat.id,
    )
    await safe_callback_answer(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await deliver_create_confirm(
        callback.message,
        bot,
        user_id=callback.from_user.id,
        parsed_items=pending.parsed_items,
        timezone=pending.timezone,
        delivery_chat_id=pending.delivery_chat_id,
        mention_telegram_id=mention_telegram_id,
        mention_username=mention_username,
        mention_source=mention_source,
        mention_provided=mention_provided,
        mention_pick_note=mention_pick_note,
        source_label=pending.source_label,
        heard_text=pending.heard_text,
    )


@router.callback_query(F.data.startswith("ah:"))
async def ambiguous_hour_picked(callback: CallbackQuery, bot) -> None:
    choice = callback.data.split(":", 1)[1]
    pending = pop_pending_task(callback.from_user.id)
    if not pending or pending.ambiguous_day is None:
        await safe_callback_answer(callback, "Уточнение устарело — напиши фразу заново.", show_alert=True)
        return
    if pending.ambiguous_hour is not None and choice not in ("day", "night"):
        await safe_callback_answer(callback, "Выбери ☀️ день или 🌙 ночь.", show_alert=True)
        return
    if pending.ambiguous_hour is None:
        phrase = phrase_from_day_only_choice(
            task=pending.text,
            day=pending.ambiguous_day,
            choice=choice,
        )
    else:
        phrase = phrase_from_ambiguous_choice(
            task=pending.text,
            day=pending.ambiguous_day,
            hour=pending.ambiguous_hour,
            choice=choice,
        )
    await safe_callback_answer(callback)
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
    )
