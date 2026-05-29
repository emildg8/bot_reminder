from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


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

    groq_model: str = "llama-3.1-8b-instant"
    gemini_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o-mini"


settings = Settings()
