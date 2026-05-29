import re

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.db.repository import async_session, get_or_create_user, get_reminder
from bot.keyboards.inline import confirm_reminder_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.drafts import clear_edit_pending, pop_edit_pending, set_edit_pending, store_draft
from bot.services.mention_parse import extract_leading_username, extract_mention_from_message
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.nlp.llm_parser import parse_reminder
from bot.services.reminder_utils import format_reminder_summary

router = Router()

EDIT_CMD_PATTERN = re.compile(r"^/edit(?:@\w+)?(?:\s+(\d+)\s+(.+))?$", re.DOTALL | re.IGNORECASE)


@router.message(lambda m: m.text and EDIT_CMD_PATTERN.match(m.text.strip()))
async def cmd_edit(message: Message, bot: Bot) -> None:
    match = EDIT_CMD_PATTERN.match(message.text.strip())
    reminder_id_str, new_phrase = match.group(1), match.group(2)

    if reminder_id_str is None:
        await message.answer(
            "Формат:\n"
            "<code>/edit 3 через 2 часа новый текст</code>\n\n"
            "Или нажми ✏️ в списке /list",
            reply_markup=main_menu_keyboard(),
        )
        return

    reminder_id = int(reminder_id_str)
    await _start_edit_flow(message, reminder_id, new_phrase, bot)


@router.callback_query(F.data.startswith("edit:"))
async def edit_button(callback: CallbackQuery, bot: Bot) -> None:
    reminder_id = int(callback.data.split(":", 1)[1])
    await _start_edit_flow(
        callback.message, reminder_id, phrase=None, user_id=callback.from_user.id, bot=bot
    )
    await callback.answer()


async def _start_edit_flow(
    message: Message,
    reminder_id: int,
    phrase: str | None,
    bot: Bot,
    user_id: int | None = None,
) -> None:
    uid = user_id or message.from_user.id
    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await message.answer("Напоминание не найдено.")
            return
        if reminder.created_by_telegram_id != uid:
            await message.answer("Можно редактировать только свои напоминания.")
            return
        user = await get_or_create_user(session, uid, settings.default_timezone)
        timezone = reminder.timezone or user.timezone

    if phrase:
        await _parse_and_confirm_edit(message, reminder_id, phrase, timezone, uid, bot)
        return

    set_edit_pending(uid, reminder_id)
    await message.answer(
        f"✏️ Редактирование #{reminder_id}.\n"
        "Отправь новую фразу, например:\n"
        "<code>через 1 час новый текст</code>\n"
        "<code>@user через 1 час задача</code>",
        reply_markup=main_menu_keyboard(),
    )


async def process_edit_phrase(message: Message, phrase: str, bot: Bot) -> bool:
    """Обрабатывает текст в режиме редактирования. Возвращает True если обработано."""
    reminder_id = pop_edit_pending(message.from_user.id)
    if reminder_id is None:
        return False

    async with async_session() as session:
        reminder = await get_reminder(session, reminder_id)
        if reminder is None or not reminder.is_active:
            await message.answer("Напоминание не найдено.")
            return True
        timezone = reminder.timezone

    await _parse_and_confirm_edit(message, reminder_id, phrase, timezone, message.from_user.id, bot)
    return True


def _extract_mention_from_phrase(message: Message, phrase: str) -> tuple[int | None, str | None, str]:
    if message.text and message.text.strip() == phrase.strip():
        return extract_mention_from_message(message)
    username, clean = extract_leading_username(phrase)
    return None, username, clean


async def _parse_and_confirm_edit(
    message: Message,
    reminder_id: int,
    phrase: str,
    timezone: str,
    user_id: int,
    bot: Bot,
) -> None:
    mention_id, mention_username, clean_text = _extract_mention_from_phrase(message, phrase)
    mention_telegram_id = await resolve_mention_user_id(bot, mention_id, mention_username)
    parsed = await parse_reminder((clean_text or phrase).strip(), timezone)
    if parsed is None:
        set_edit_pending(user_id, reminder_id)
        await message.answer(
            "Не понял новое время. Попробуй ещё раз, например:\n"
            "<code>через 30 минут новый текст</code>"
        )
        return

    clear_edit_pending(user_id)
    summary = format_reminder_summary(parsed, timezone)
    prefix = ""
    if mention_username and not mention_telegram_id:
        prefix = f"⚠️ @{mention_username} не найден — упоминание сброшено.\n\n"
    elif mention_telegram_id:
        who = f"@{mention_username}" if mention_username else "участнику"
        prefix = f"👤 Упоминание: {who}\n\n"

    mention_provided = bool(mention_username or mention_id)
    draft_id = store_draft(
        user_id,
        parsed,
        mention_telegram_id=mention_telegram_id,
        mention_provided=mention_provided,
        edit_reminder_id=reminder_id,
    )
    await message.answer(
        f"✏️ Изменить #{reminder_id}?\n\n{prefix}{summary}\n\nПодтверди изменение:",
        reply_markup=confirm_reminder_keyboard(draft_id, edit_id=reminder_id),
    )
