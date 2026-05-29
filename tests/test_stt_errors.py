import subprocess

from bot.services.stt_errors import format_stt_error


def test_ffmpeg_error():
    msg = format_stt_error(subprocess.CalledProcessError(1, "ffmpeg"))
    assert "ffmpeg" in msg.lower()


def test_runtime_recognize():
    msg = format_stt_error(RuntimeError("Не удалось распознать аудио"))
    assert "распознать" in msg.lower() or "текст" in msg.lower()


def test_generic():
    msg = format_stt_error(Exception("internal"))
    assert "internal" not in msg
