from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

# Встроенные админы (дополняют ADMIN_TELEGRAM_IDS из .env)
BUILTIN_ADMIN_TELEGRAM_IDS: tuple[int, ...] = (292396648,)


def _parse_admin_ids(value: Any) -> list[int]:
    if value is None or value == "" or value == []:
        return []
    if isinstance(value, int):
        return [value]
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        return [int(p) for p in parts]
    if isinstance(value, (list, tuple)):
        return [int(x) for x in value]
    raise ValueError(f"Invalid admin_telegram_ids: {value!r}")


def _merge_admin_ids(parsed: list[int]) -> list[int]:
    seen: set[int] = set()
    merged: list[int] = []
    for uid in (*BUILTIN_ADMIN_TELEGRAM_IDS, *parsed):
        if uid not in seen:
            seen.add(uid)
            merged.append(uid)
    return merged


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'reminders.db'}"

    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    whisper_model: str = "tiny"
    whisper_device: str = "cpu"
    local_whisper_enabled: bool = False
    use_yandex_stt: bool = False
    yandex_api_key: str = ""
    yandex_folder_id: str = ""

    default_timezone: str = "Europe/Moscow"

    log_max_bytes: int = 2 * 1024 * 1024
    log_backup_count: int = 2

    db_backup_keep: int = 7
    db_backup_interval_hours: int = 24

    bot_description: str = (
        "⏰ Напоминалка — не забывай важное.\n\n"
        "• Текст, голос или кружочек\n"
        "• Разовые, ежедневные, интервалы, будни\n"
        "• Дневник, история, статистика\n"
        "• Личка и группы · /help · /about"
    )
    bot_short_description: str = "⏰ Напоминания, дневник и статистика"

    admin_telegram_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    github_repo: str = "emildg8/bot_reminder"
    github_branch: str = "main"
    auto_update_enabled: bool = True
    auto_update_interval_minutes: int = 1

    stars_tips_enabled: bool = False
    stars_tip_presets: str = "25,50,100,250,500"
    stars_tip_min: int = 1
    stars_tip_max: int = 2500
    stars_tips_notify_admin: bool = True
    stars_tip_nudge_enabled: bool = True
    stars_tip_nudge_days: int = 14
    stars_tip_nudge_min_dones: int = 3
    stars_tip_nudge_once: bool = True

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, value: Any) -> list[int]:
        return _parse_admin_ids(value)

    @field_validator("admin_telegram_ids", mode="after")
    @classmethod
    def merge_builtin_admin_ids(cls, value: list[int]) -> list[int]:
        return _merge_admin_ids(value)

    def stars_tip_preset_list(self) -> list[int]:
        values: list[int] = []
        for part in self.stars_tip_presets.split(","):
            part = part.strip()
            if part.isdigit():
                n = int(part)
                if n > 0:
                    values.append(n)
        return values or [50, 100, 250]

    groq_model: str = "llama-3.1-8b-instant"
    groq_whisper_model: str = "whisper-large-v3-turbo"
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o-mini"


settings = Settings()
