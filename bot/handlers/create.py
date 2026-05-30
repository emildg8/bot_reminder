import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.db.repository import async_session
from bot.services.stt_errors import format_stt_error
from bot.services.timezone_ctx import get_effective_timezone
from bot.handlers.edit import process_edit_phrase
from bot.keyboards.inline import confirm_reminder_keyboard, task_time_keyboard
from bot.keyboards.reply import MENU_BUTTON_TEXTS, main_menu_keyboard
from bot.services.drafts import store_draft
from bot.services.pending_tasks import store_pending_task
from bot.services.reminder_display import format_parsed_summary_html
from bot.texts.messages import format_confirm_card, format_parse_fail, looks_like_task_only
from bot.services.media import (
    download_telegram_file,
    extract_audio_from_video,
    transcribe_audio,
)
from bot.services.mention_parse import extract_leading_username, extract_mention_from_message
from bot.services.mention_resolve import resolve_mention_user_id
from bot.services.nlp.llm_parser import parse_reminder

logger = logging.getLogger(__name__)
router = Router()


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

    if use_phrase_text or source_label:
        mention_id, mention_username, clean_text = None, None, text
        u, cleaned = extract_leading_username(text)
        if u:
            mention_username = u
            clean_text = cleaned
    else:
        mention_id, mention_username, clean_text = extract_mention_from_message(message)

    mention_telegram_id = await resolve_mention_user_id(bot, mention_id, mention_username)
    phrase = (clean_text or text).strip()

    timezone = await _get_parse_timezone(message.chat.id, user_id)
    parsed = await parse_reminder(phrase, timezone)

    if parsed is None:
        if looks_like_task_only(phrase):
            store_pending_task(user_id, phrase)
            await message.answer(
                format_parse_fail(phrase),
                reply_markup=task_time_keyboard(),
            )
        else:
            await message.answer(
                format_parse_fail(phrase),
                reply_markup=main_menu_keyboard(),
            )
        return

    summary = format_parsed_summary_html(parsed, timezone)
    prefix = f"🎤 Распознано: {text}\n\n" if source_label else ""
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
        parsed,
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


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTON_TEXTS))
async def handle_text(message: Message, bot: Bot) -> None:
    text = message.text.strip()
    if await process_edit_phrase(message, text, bot):
        return
    await _process_text_and_reply(message, text, bot)


async def _handle_audio_message(message: Message, bot: Bot, file_id: str, suffix: str, is_video: bool) -> None:
    status = await message.answer("🎧 Распознаю...")
    audio_path: Path | None = None
    video_path: Path | None = None

    try:
        if is_video:
            video_path = await download_telegram_file(bot, file_id, suffix=".mp4")
            audio_path = await extract_audio_from_video(video_path)
        else:
            audio_path = await download_telegram_file(bot, file_id, suffix=suffix)

        text = await transcribe_audio(audio_path)
        if not text:
            await status.edit_text("Не удалось распознать речь. Попробуй ещё раз.")
            return

        await status.delete()
        await _process_text_and_reply(message, text, bot, source_label="voice")
    except Exception as exc:
        logger.exception("STT failed")
        await status.edit_text(format_stt_error(exc))
    finally:
        for path in (audio_path, video_path):
            if path and path.exists():
                path.unlink(missing_ok=True)


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot) -> None:
    await _handle_audio_message(message, bot, message.voice.file_id, suffix=".ogg", is_video=False)


@router.message(F.video_note)
async def handle_video_note(message: Message, bot: Bot) -> None:
    await _handle_audio_message(message, bot, message.video_note.file_id, suffix=".mp4", is_video=True)
