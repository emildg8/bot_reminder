from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


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
        "• Разовые, ежедневные, по будням, интервалы\n"
        "• Личка и группы · /help"
    )
    bot_short_description: str = "⏰ Напоминания текстом, голосом и по расписанию"

    admin_telegram_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def parse_admin_telegram_ids(cls, value: Any) -> list[int]:
        return _parse_admin_ids(value)

    groq_model: str = "llama-3.1-8b-instant"
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o-mini"


settings = Settings()
