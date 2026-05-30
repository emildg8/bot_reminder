from unittest.mock import AsyncMock, patch

import pytest

from bot.services.media import describe_stt_backends, transcribe_audio


def test_describe_stt_backends_with_groq(monkeypatch):
    from bot.config import settings

    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(settings, "use_yandex_stt", False)
    chain = describe_stt_backends()
    assert "Groq" in chain
    assert "Whisper local" in chain


@pytest.mark.asyncio
async def test_transcribe_prefers_groq(tmp_path, monkeypatch):
    from bot.config import settings

    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    audio = tmp_path / "voice.ogg"
    audio.write_bytes(b"fake")

    with patch(
        "bot.services.media.GroqWhisperSTT.transcribe",
        new=AsyncMock(return_value="через час таблетки"),
    ) as groq_mock:
        text = await transcribe_audio(audio)

    assert text == "через час таблетки"
    groq_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_transcribe_falls_back_to_whisper(tmp_path, monkeypatch):
    from bot.config import settings

    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "use_yandex_stt", False)
    audio = tmp_path / "voice.wav"
    audio.write_bytes(b"fake")

    with (
        patch(
            "bot.services.media.convert_to_wav",
            new=AsyncMock(return_value=audio),
        ),
        patch(
            "bot.services.media.WhisperLocalSTT.transcribe",
            new=AsyncMock(return_value="завтра в 9 зарядка"),
        ) as whisper_mock,
    ):
        text = await transcribe_audio(audio)

    assert text == "завтра в 9 зарядка"
    whisper_mock.assert_awaited_once()
