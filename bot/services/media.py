import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path

from aiogram import Bot

from bot.config import settings
from bot.services.stt.whisper_local import WhisperLocalSTT
from bot.services.stt.yandex import YandexSTT

logger = logging.getLogger(__name__)


async def download_telegram_file(bot: Bot, file_id: str, suffix: str) -> Path:
    file = await bot.get_file(file_id)
    if file.file_path is None:
        raise ValueError("Telegram file path is empty")

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp.name)
    temp.close()

    await bot.download_file(file.file_path, destination=temp_path)
    return temp_path


def _extract_audio_sync(video_path: Path) -> Path:
    output = video_path.with_suffix(".wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output


async def extract_audio_from_video(video_path: Path) -> Path:
    return await asyncio.to_thread(_extract_audio_sync, video_path)


async def transcribe_audio(audio_path: Path, language: str = "ru") -> str:
    whisper = WhisperLocalSTT()
    try:
        text = await whisper.transcribe(str(audio_path), language=language)
        if text:
            return text
    except Exception as exc:
        logger.warning("Whisper STT failed: %s", exc)

    if settings.use_yandex_stt and settings.yandex_api_key and settings.yandex_folder_id:
        yandex = YandexSTT()
        return await yandex.transcribe(str(audio_path), language=language)

    raise RuntimeError("Не удалось распознать аудио")
