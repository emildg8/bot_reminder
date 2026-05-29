import asyncio
import logging

import httpx

from bot.config import settings
from bot.services.stt.base import STTProvider

logger = logging.getLogger(__name__)


def _recognize_sync(audio_path: str, language: str) -> str:
    with open(audio_path, "rb") as audio_file:
        audio_data = audio_file.read()

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    params = {
        "lang": "ru-RU" if language == "ru" else "en-US",
        "folderId": settings.yandex_folder_id,
    }
    headers = {"Authorization": f"Api-Key {settings.yandex_api_key}"}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, params=params, headers=headers, content=audio_data)
        response.raise_for_status()
        data = response.json()
        return data.get("result", "").strip()


class YandexSTT(STTProvider):
    async def transcribe(self, audio_path: str, language: str = "ru") -> str:
        return await asyncio.to_thread(_recognize_sync, audio_path, language)
