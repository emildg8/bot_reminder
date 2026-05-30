"""Очистка и нормализация текста после STT перед парсингом."""

from __future__ import annotations

import re

from bot.services.nlp.absolute_time_parse import normalize_phrase

_YO = str.maketrans("ёЁ", "еЕ")

# Паразитные слова и паузы в голосовых
_FILLERS = re.compile(
    r"^(?:\s*(?:э+|м+|ну|в\s+общем|то\s+есть|типа|как\s+бы|значит|смотри)\s*[,]?\s*)+",
    re.IGNORECASE,
)
_REMINDER_FILLER = re.compile(
    r"^(?:"
    r"напомни(?:ть|м)?(?:\s+мне)?|напомню(?:\s+мне)?|напомним|"
    r"запомни(?:ть|м)?|поставь(?:\s+напоминание)?"
    r")\s*[,]?\s*",
    re.IGNORECASE,
)
# «14 00», «2 0 0» — типичный вывод Whisper
_SPACED_TIME = re.compile(r"\b(\d{1,2})\s+(\d{2})\b")
# «14-00» → «14:00»
_DASH_TIME = re.compile(r"\b(\d{1,2})[-–—](\d{2})\b")
# Частые ошибки STT
_STT_TYPOS = (
    (re.compile(r"\bпара\s+час", re.I), "пару час"),
    (re.compile(r"\bпару\s+минут\b", re.I), "пару минут"),
    (re.compile(r"\bзапомни\b", re.I), "напомни"),
    (re.compile(r"\bна\s+помни\b", re.I), "напомни"),
)

MIN_STT_WORDS = 2


def cleanup_stt_text(text: str) -> str:
    cleaned = text.translate(_YO).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s*,\s*", ", ", cleaned)
    cleaned = _FILLERS.sub("", cleaned)
    cleaned = _REMINDER_FILLER.sub("", cleaned)
    for pattern, repl in _STT_TYPOS:
        cleaned = pattern.sub(repl, cleaned)
    cleaned = _SPACED_TIME.sub(r"\1:\2", cleaned)
    cleaned = _DASH_TIME.sub(r"\1:\2", cleaned)
    cleaned = cleaned.strip(" ,.")
    return normalize_phrase(cleaned)


def is_stt_text_too_short(text: str) -> bool:
    return len(text.split()) < MIN_STT_WORDS
