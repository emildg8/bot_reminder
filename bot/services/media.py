import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from aiogram import Bot

from bot.config import settings
from bot.services.stt.groq import GroqWhisperSTT
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


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _convert_to_wav_sync(input_path: Path) -> Path:
    output = input_path.with_name(f"{input_path.stem}_stt.wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
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


async def convert_to_wav(input_path: Path) -> Path:
    if input_path.suffix.lower() == ".wav":
        return input_path
    return await asyncio.to_thread(_convert_to_wav_sync, input_path)


async def extract_audio_from_video(video_path: Path) -> Path:
    return await convert_to_wav(video_path)


def describe_stt_backends() -> str:
    parts: list[str] = []
    if settings.groq_api_key:
        parts.append(f"Groq ({settings.groq_whisper_model})")
    parts.append(f"Whisper local ({settings.whisper_model})")
    if settings.use_yandex_stt and settings.yandex_api_key and settings.yandex_folder_id:
        parts.append("Yandex")
    return " → ".join(parts)


async def transcribe_audio(audio_path: Path, language: str = "ru") -> str:
    if settings.groq_api_key:
        try:
            text = await GroqWhisperSTT().transcribe(str(audio_path), language=language)
            if text:
                return text
        except Exception as exc:
            logger.warning("Groq STT failed: %s", exc)

    wav_path: Path | None = None
    try:
        if audio_path.suffix.lower() == ".wav":
            stt_path = audio_path
        else:
            wav_path = await convert_to_wav(audio_path)
            stt_path = wav_path

        try:
            text = await WhisperLocalSTT().transcribe(str(stt_path), language=language)
            if text:
                return text
        except Exception as exc:
            logger.warning("Whisper STT failed: %s", exc)

        if settings.use_yandex_stt and settings.yandex_api_key and settings.yandex_folder_id:
            text = await YandexSTT().transcribe(str(stt_path), language=language)
            if text:
                return text
    finally:
        if wav_path and wav_path != audio_path and wav_path.exists():
            wav_path.unlink(missing_ok=True)

    raise RuntimeError("Не удалось распознать аудио")
