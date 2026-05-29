"""Дружелюбные сообщения об ошибках STT."""

from __future__ import annotations

import subprocess


def format_stt_error(exc: Exception) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        return (
            "Не удалось обработать аудио (ffmpeg). "
            "Попробуй текстом или обратись к админу сервера."
        )
    if isinstance(exc, FileNotFoundError):
        return "На сервере не установлен ffmpeg. Пока используй текстовые напоминания."

    msg = str(exc).lower()
    if "ffmpeg" in msg:
        return "Ошибка ffmpeg при обработке кружочка. Попробуй голосовое или текст."

    if isinstance(exc, RuntimeError) and "распознать" in str(exc).lower():
        return "Не удалось распознать речь. Говори чётче или напиши текстом."

    if isinstance(exc, ValueError):
        return "Не удалось скачать файл из Telegram. Попробуй ещё раз."

    return "Ошибка распознавания. Попробуй ещё раз или напиши текстом."
