import asyncio
import logging

from bot.config import settings
from bot.services.stt.base import STTProvider

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        logger.info("Loading Whisper model: %s", settings.whisper_model)
        _model = WhisperModel(settings.whisper_model, device=settings.whisper_device, compute_type="int8")
    return _model


def _transcribe_sync(audio_path: str, language: str) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio_path, language=language, beam_size=1)
    return " ".join(segment.text.strip() for segment in segments).strip()


class WhisperLocalSTT(STTProvider):
    async def transcribe(self, audio_path: str, language: str = "ru") -> str:
        return await asyncio.to_thread(_transcribe_sync, audio_path, language)
