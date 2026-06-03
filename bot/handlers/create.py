import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.handlers.filters import USER_PHRASE_TEXT

from bot.db.repository import async_session
from bot.handlers.edit import process_edit_phrase
from bot.keyboards.inline import task_time_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.bot_mention import should_handle_collective_message
from bot.services.assignee_prompt import offer_assignee_choice
from bot.services.create_confirm import deliver_create_confirm
from bot.services.chat_ctx import ChatKind, chat_kind_from_chat, is_group_chat
from bot.services.chat_delivery import resolve_delivery_chat_id
from bot.services.stt_errors import format_stt_error
from bot.services.timezone_ctx import get_effective_timezone
from bot.services.drafts import pop_search_pending
from bot.services.pending_tasks import get_pending_task, store_pending_task
from bot.services.mention_parse import extract_username_candidates, strip_leading_bot_mention
from bot.services.pending_assignee import clear_pending_assignee
from bot.services.search_ui import send_search_results
from bot.texts.messages import (
    format_parse_fail,
    format_pending_ambiguous_hint,
    looks_like_task_only,
)
from bot.services.ambiguous_prompt import offer_ambiguous_time_choice
from bot.services.media import download_telegram_file, transcribe_audio
from bot.services.mention_create import extract_create_mention, mention_was_provided
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.nlp.llm_parser import parse_all_reminders
from bot.services.nlp.speech_cleanup import cleanup_stt_text, is_stt_text_too_short

logger = logging.getLogger(__name__)
router = Router()

MAX_VOICE_SECONDS = 120
MAX_VIDEO_NOTE_SECONDS = 60
MIN_AUDIO_SECONDS = 1


def _message_text_or_caption(message: Message) -> str | None:
    """Реальный текст сообщения (callback.message часто MagicMock без str)."""
    text = getattr(message, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    caption = getattr(message, "caption", None)
    if isinstance(caption, str) and caption.strip():
        return caption.strip()
    return None


def _raw_for_assignee_candidates(
    message: Message, phrase_text: str, *, source_label: str
) -> str:
    """Текст для поиска @user: в голосе — распознанная фраза, иначе сообщение."""
    if source_label in ("voice", "video_note"):
        return phrase_text.strip()
    from_msg = _message_text_or_caption(message)
    if from_msg is not None:
        return from_msg
    return phrase_text.strip()


async def _get_parse_timezone(chat_id: int, user_id: int) -> str:
    async with async_session() as session:
        return await get_effective_timezone(session, chat_id, user_id)


async def _resolve_delivery(message: Message) -> int:
    async with async_session() as session:
        return await resolve_delivery_chat_id(
            session, message.chat.id, message.chat.type
        )


async def _process_text_and_reply(
    message: Message,
    text: str,
    bot: Bot,
    source_label: str = "",
    *,
    actor_user_id: int | None = None,
) -> None:
    user_id = actor_user_id or message.from_user.id
    clear_pending_assignee(user_id)
    me = await bot.get_me()

    mention = extract_create_mention(
        message,
        text,
        bot_username=me.username,
        bot_id=me.id,
        from_transcription=source_label in ("voice", "video_note"),
    )
    if is_group_chat(message.chat.id) and (mention.source or mention.username):
        logger.info(
            "Group assignee chat=%s user=%s source=%s id=%s name=%s phrase=%s",
            message.chat.id,
            user_id,
            mention.source,
            mention.user_id,
            mention.username,
            mention.phrase[:80],
        )
    mention_telegram_id = await resolve_mention_user_id(
        bot, mention.user_id, mention.username, chat_id=message.chat.id
    )
    phrase = mention.phrase

    delivery_chat_id = await _resolve_delivery(message)
    async with async_session() as session:
        timezone = await get_effective_timezone(session, delivery_chat_id, user_id)

    if await offer_ambiguous_time_choice(message, phrase, user_id):
        return

    parsed_items = await parse_all_reminders(phrase, timezone)

    if not parsed_items:
        chat_kind = chat_kind_from_chat(message.chat)
        fail_kwargs = {
            "source": source_label,
            "heard": text if source_label else "",
            "chat_kind": chat_kind,
            "bot_username": me.username,
        }
        if looks_like_task_only(phrase):
            store_pending_task(user_id, phrase)
            await message.answer(
                format_parse_fail(phrase, **fail_kwargs),
                reply_markup=task_time_keyboard(),
            )
        else:
            await message.answer(
                format_parse_fail(phrase, **fail_kwargs),
                reply_markup=menu_keyboard_for_chat(message.chat.id),
            )
        return

    raw = _raw_for_assignee_candidates(message, text, source_label=source_label)
    candidates, _ = extract_username_candidates(raw, me.username)
    if await offer_assignee_choice(
        message,
        user_id=user_id,
        parsed_items=parsed_items,
        phrase=phrase,
        candidates=candidates,
        timezone=timezone,
        delivery_chat_id=delivery_chat_id,
        source_label=source_label,
        heard_text=text,
    ):
        return

    mention_resolved = mention_telegram_id is not None or not mention.username
    await deliver_create_confirm(
        message,
        bot,
        user_id=user_id,
        parsed_items=parsed_items,
        timezone=timezone,
        delivery_chat_id=delivery_chat_id,
        mention_telegram_id=mention_telegram_id,
        mention_username=mention.username,
        mention_source=mention.source,
        mention_provided=mention_was_provided(mention),
        mention_pick_note=mention.pick_note,
        source_label=source_label,
        heard_text=text,
        mention_resolved=mention_resolved,
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
    pending = get_pending_task(message.from_user.id)
    if pending and pending.ambiguous_day is not None:
        await message.answer(format_pending_ambiguous_hint())
        return
    if await process_edit_phrase(message, text, bot):
        return
    await _process_text_and_reply(message, text, bot, source_label=source_label)


@router.message(Command("remind"))
async def cmd_remind(message: Message, command: CommandObject, bot: Bot) -> None:
    phrase = (command.args or "").strip()
    kind = chat_kind_from_chat(message.chat)
    if not phrase:
        me = await bot.get_me()
        uname = me.username or "бот"
        if kind == ChatKind.CHANNEL:
            await message.answer(
                "✍️ <b>Напоминание в канале</b>\n\n"
                f"<code>/remind@{uname} завтра в 10:00 пост</code>\n"
                f"<code>/remind@{uname} через 2 часа проверить</code>\n\n"
                "Кнопки «Отложить / Готово» — в личке у создавшего админа."
            )
            return
        await message.answer(
            "✍️ <b>Создать напоминание в группе</b>\n\n"
            f"<code>/remind@{uname} завтра в 14:00 созвон</code>\n"
            f"<code>/remind@{uname} @user завтра в 14:00 задача</code>\n"
            "↩️ Ответ на сообщение + <code>/remind …</code> — напоминание этому человеку\n\n"
            "👤 @user или <b>имя из списка</b> (@ → тап по участнику) — не просто набор имени."
        )
        return
    await _process_text_and_reply(message, phrase, bot)


async def _handle_collective_phrase_message(message: Message, bot: Bot) -> None:
    """Текст в личке или @бот в группе (в т.ч. после правки сообщения)."""
    me = await bot.get_me()
    if not should_handle_collective_message(
        message, bot_username=me.username, bot_id=me.id
    ):
        return

    raw_text = (message.text or "").strip()
    if is_group_chat(message.chat.id):
        logger.info(
            "Group text chat=%s user=%s: %s",
            message.chat.id,
            message.from_user.id if message.from_user else "?",
            raw_text[:120],
        )
    text = strip_leading_bot_mention(raw_text, me.username)
    await _route_user_phrase(message, text, bot)


@router.message(USER_PHRASE_TEXT)
async def handle_text(message: Message, bot: Bot) -> None:
    try:
        await _handle_collective_phrase_message(message, bot)
    except Exception:
        logger.exception("Failed to handle text in chat %s", message.chat.id)
        await message.answer(
            "⚠️ Не удалось обработать сообщение. Попробуй ещё раз или <code>/ping</code>."
        )


@router.edited_message(USER_PHRASE_TEXT)
async def handle_edited_text(message: Message, bot: Bot) -> None:
    try:
        await _handle_collective_phrase_message(message, bot)
    except Exception:
        logger.exception("Failed to handle edited text in chat %s", message.chat.id)
        await message.answer(
            "⚠️ Не удалось обработать правку. Попробуй ещё раз или <code>/ping</code>."
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

    me = await bot.get_me()
    if not should_handle_collective_message(message, bot_username=me.username, bot_id=me.id):
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
        if is_group_chat(message.chat.id):
            text = strip_leading_bot_mention(text, me.username)
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
