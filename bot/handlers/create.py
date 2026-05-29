import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.db.repository import async_session, get_or_create_user
from bot.keyboards.inline import confirm_reminder_keyboard
from bot.services.drafts import store_draft
from bot.services.media import (
    download_telegram_file,
    extract_audio_from_video,
    transcribe_audio,
)
from bot.services.nlp.llm_parser import parse_reminder
from bot.services.reminder_utils import format_reminder_summary

logger = logging.getLogger(__name__)
router = Router()


async def _get_user_timezone(telegram_id: int) -> str:
    from bot.config import settings

    async with async_session() as session:
        user = await get_or_create_user(session, telegram_id, settings.default_timezone)
        return user.timezone


async def _process_text_and_reply(message: Message, text: str, source_label: str = "") -> None:
    timezone = await _get_user_timezone(message.from_user.id)
    parsed = await parse_reminder(text, timezone)

    if parsed is None:
        await message.answer(
            "Не понял время. Напиши, например:\n"
            "• через 30 минут выпить таблетки\n"
            "• каждый день в 9:00 зарядка\n"
            "• каждые 2 часа встать"
        )
        return

    summary = format_reminder_summary(parsed, timezone)
    prefix = f"🎤 Распознано: {text}\n\n" if source_label else ""
    draft_id = store_draft(message.from_user.id, parsed)

    await message.answer(
        f"{prefix}{summary}\n\nСоздать напоминание?",
        reply_markup=confirm_reminder_keyboard(draft_id),
    )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message) -> None:
    await _process_text_and_reply(message, message.text.strip())


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
        await _process_text_and_reply(message, text, source_label="voice")
    except Exception as exc:
        logger.exception("STT failed")
        await status.edit_text(f"Ошибка распознавания: {exc}")
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
