import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.db.repository import async_session
from bot.services.bot_mention import should_handle_group_text
from bot.services.stt_errors import format_stt_error
from bot.services.timezone_ctx import get_effective_timezone
from bot.handlers.edit import process_edit_phrase
from bot.keyboards.inline import confirm_reminder_keyboard, task_time_keyboard
from bot.keyboards.reply import MENU_BUTTON_TEXTS, menu_keyboard_for_chat
from bot.services.timezone_ctx import is_group_chat
from bot.services.drafts import pop_search_pending, store_draft
from bot.services.pending_tasks import store_pending_task
from bot.services.reminder_display import format_batch_parsed_summary_html
from bot.services.search_ui import send_search_results
from bot.texts.messages import format_confirm_card, format_parse_fail, looks_like_task_only
from bot.services.media import download_telegram_file, transcribe_audio
from bot.services.mention_parse import extract_leading_username, extract_mention_from_message
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.nlp.llm_parser import parse_all_reminders
from bot.services.nlp.speech_cleanup import cleanup_stt_text, is_stt_text_too_short

logger = logging.getLogger(__name__)
router = Router()

MAX_VOICE_SECONDS = 120
MAX_VIDEO_NOTE_SECONDS = 60
MIN_AUDIO_SECONDS = 1


async def _get_parse_timezone(chat_id: int, user_id: int) -> str:
    async with async_session() as session:
        return await get_effective_timezone(session, chat_id, user_id)


async def _process_text_and_reply(
    message: Message,
    text: str,
    bot: Bot,
    source_label: str = "",
    *,
    actor_user_id: int | None = None,
    use_phrase_text: bool = False,
) -> None:
    user_id = actor_user_id or message.from_user.id
    me = await bot.get_me()

    if use_phrase_text or source_label:
        mention_id, mention_username, clean_text = None, None, text
        u, cleaned = extract_leading_username(text, me.username)
        if u:
            mention_username = u
            clean_text = cleaned
    else:
        mention_id, mention_username, clean_text = extract_mention_from_message(
            message,
            bot_username=me.username,
            bot_id=me.id,
        )

    mention_telegram_id = await resolve_mention_user_id(bot, mention_id, mention_username)
    phrase = (clean_text or text).strip()

    timezone = await _get_parse_timezone(message.chat.id, user_id)
    parsed_items = await parse_all_reminders(phrase, timezone)

    if not parsed_items:
        if looks_like_task_only(phrase):
            store_pending_task(user_id, phrase)
            await message.answer(
                format_parse_fail(phrase, source=source_label, heard=text if source_label else ""),
                reply_markup=task_time_keyboard(),
            )
        else:
            await message.answer(
                format_parse_fail(phrase, source=source_label, heard=text if source_label else ""),
                reply_markup=menu_keyboard_for_chat(message.chat.id),
            )
        return

    summary = format_batch_parsed_summary_html(parsed_items, timezone)
    if source_label == "voice":
        prefix = f"🎤 Распознано: {text}\n\n"
    elif source_label == "video_note":
        prefix = f"🔵 Из кружочка: {text}\n\n"
    else:
        prefix = ""
    if mention_username and not mention_telegram_id:
        prefix += (
            f"⚠️ Не удалось найти @{mention_username} — "
            "в группе напомню создателю.\n\n"
        )
    elif mention_telegram_id or mention_username:
        who = f"@{mention_username}" if mention_username else "участнику"
        prefix += f"👤 Упоминание: {who}\n\n"

    mention_provided = bool(mention_username or mention_id)
    draft_id = store_draft(
        user_id,
        parsed_items=parsed_items,
        mention_telegram_id=mention_telegram_id,
        mention_provided=mention_provided,
    )

    body = format_confirm_card(summary)
    if prefix:
        body = prefix + body
    await message.answer(
        body,
        reply_markup=confirm_reminder_keyboard(draft_id),
    )


async def _route_user_phrase(
    message: Message,
    text: str,
    bot: Bot,
    *,
    source_label: str = "",
) -> None:
    if pop_search_pending(message.from_user.id):
        await send_search_results(message, text)
        return
    if await process_edit_phrase(message, text, bot):
        return
    await _process_text_and_reply(message, text, bot, source_label=source_label)


@router.message(Command("remind"))
async def cmd_remind(message: Message, command: CommandObject, bot: Bot) -> None:
    phrase = (command.args or "").strip()
    if not phrase:
        me = await bot.get_me()
        uname = me.username or "бот"
        await message.answer(
            "✍️ <b>Создать напоминание в группе</b>\n\n"
            f"<code>/remind@{uname} завтра в 14:00 созвон</code>\n"
            f"<code>/remind@{uname} через 30 минут таблетки</code>\n\n"
            f"💡 Если пишешь через @ — выбери <code>@{uname}</code> из списка, "
            "не набирай @ вручную."
        )
        return
    await _route_user_phrase(message, phrase, bot)


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTON_TEXTS))
async def handle_text(message: Message, bot: Bot) -> None:
    try:
        me = await bot.get_me()
        if not should_handle_group_text(
            message, bot_username=me.username, bot_id=me.id
        ):
            return

        if is_group_chat(message.chat.id):
            logger.info(
                "Group text chat=%s user=%s: %s",
                message.chat.id,
                message.from_user.id if message.from_user else "?",
                (message.text or "")[:120],
            )
        await _route_user_phrase(message, message.text.strip(), bot)
    except Exception:
        logger.exception("Failed to handle text in chat %s", message.chat.id)
        await message.answer(
            "⚠️ Не удалось обработать сообщение. Попробуй ещё раз или <code>/ping</code>."
        )


async def _handle_audio_message(
    message: Message,
    bot: Bot,
    file_id: str,
    *,
    suffix: str,
    source_label: str,
    max_seconds: int,
    duration: int | None,
) -> None:
    if duration is not None:
        if duration < MIN_AUDIO_SECONDS:
            await message.answer("Слишком короткое сообщение. Скажи фразу с задачей и временем.")
            return
        if duration > max_seconds:
            await message.answer(
                f"Слишком длинно ({duration} с). "
                f"Короче {max_seconds} с — одной фразой с задачей и временем."
            )
            return

    status = await message.answer("🎧 Распознаю...")
    raw_path: Path | None = None

    try:
        raw_path = await download_telegram_file(bot, file_id, suffix=suffix)
        text = await transcribe_audio(raw_path)
        if not text:
            await status.edit_text("Не удалось распознать речь. Попробуй ещё раз.")
            return

        if source_label in ("voice", "video_note"):
            text = cleanup_stt_text(text)
            if is_stt_text_too_short(text):
                await status.edit_text(
                    "Распознал слишком мало текста.\n"
                    "Скажи одной фразой: <b>когда</b> и <b>что</b>, "
                    "например «завтра в два часа дня созвон»."
                )
                return

        await status.delete()
        await _route_user_phrase(message, text, bot, source_label=source_label)
    except Exception as exc:
        logger.exception("STT failed")
        await status.edit_text(format_stt_error(exc))
    finally:
        if raw_path and raw_path.exists():
            raw_path.unlink(missing_ok=True)


@router.message(F.audio)
async def handle_audio(message: Message, bot: Bot) -> None:
    audio = message.audio
    suffix = ".mp3"
    if audio.file_name and "." in audio.file_name:
        suffix = Path(audio.file_name).suffix or suffix
    await _handle_audio_message(
        message,
        bot,
        audio.file_id,
        suffix=suffix,
        source_label="voice",
        max_seconds=MAX_VOICE_SECONDS,
        duration=audio.duration,
    )


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot) -> None:
    voice = message.voice
    await _handle_audio_message(
        message,
        bot,
        voice.file_id,
        suffix=".ogg",
        source_label="voice",
        max_seconds=MAX_VOICE_SECONDS,
        duration=voice.duration,
    )


@router.message(F.video_note)
async def handle_video_note(message: Message, bot: Bot) -> None:
    note = message.video_note
    await _handle_audio_message(
        message,
        bot,
        note.file_id,
        suffix=".mp4",
        source_label="video_note",
        max_seconds=MAX_VIDEO_NOTE_SECONDS,
        duration=note.duration,
    )
