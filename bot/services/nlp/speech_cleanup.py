"""Лёгкая очистка текста после STT перед парсингом."""

from __future__ import annotations

import re


def cleanup_stt_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    return cleaned.strip(" ,.")
