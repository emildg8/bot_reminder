import asyncio
import logging
from pathlib import Path

import httpx

from bot.config import settings
from bot.services.stt.base import STTProvider

logger = logging.getLogger(__name__)


def _transcribe_sync(audio_path: str, language: str) -> str:
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    filename = Path(audio_path).name

    with open(audio_path, "rb") as audio_file:
        files = {"file": (filename, audio_file)}
        data = {
            "model": settings.groq_whisper_model,
            "language": language,
            "response_format": "json",
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            payload = response.json()

    text = payload.get("text", "")
    return text.strip() if isinstance(text, str) else ""


class GroqWhisperSTT(STTProvider):
    async def transcribe(self, audio_path: str, language: str = "ru") -> str:
        return await asyncio.to_thread(_transcribe_sync, audio_path, language)
