from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

from bot.services.nlp.schemas import ParsedReminder


def once_parsed(text: str = "тест", *, hour: int = 12) -> ParsedReminder:
    tz = ZoneInfo("Europe/Moscow")
    return ParsedReminder(
        text=text,
        kind="once",
        run_at=datetime(2030, 1, 15, hour, 0, tzinfo=tz),
    )


def make_callback(data: str, user_id: int, chat_id: int | None = None) -> MagicMock:
    chat_id = chat_id if chat_id is not None else user_id
    callback = MagicMock()
    callback.data = data
    callback.from_user.id = user_id
    callback.from_user.username = "tester"
    callback.message.from_user = callback.from_user
    callback.message.chat.id = chat_id
    callback.message.chat.type = "private"
    callback.message.edit_text = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    return callback


def make_message(user_id: int, chat_id: int | None = None) -> MagicMock:
    chat_id = chat_id if chat_id is not None else user_id
    message = MagicMock()
    message.from_user.id = user_id
    message.from_user.username = "tester"
    message.chat.id = chat_id
    message.chat.type = "private"
    message.answer = AsyncMock()
    return message


def make_bot(*, username: str = "testbot", bot_id: int = 1) -> AsyncMock:
    bot = AsyncMock()
    me = AsyncMock()
    me.username = username
    me.id = bot_id
    bot.get_me = AsyncMock(return_value=me)
    return bot


def patch_scheduler(monkeypatch) -> list:
    scheduled: list[tuple[int, datetime]] = []

    def fake_schedule(bot, reminder_id, next_run, *, timezone=None):
        scheduled.append((reminder_id, next_run))

    monkeypatch.setattr("bot.services.reminder_create.schedule_reminder", fake_schedule)
    monkeypatch.setattr("bot.handlers.callbacks.schedule_reminder", fake_schedule)
    monkeypatch.setattr(
        "bot.services.reminder_create.setup_channel_telegram_schedule",
        AsyncMock(),
    )
    monkeypatch.setattr("bot.handlers.callbacks.setup_channel_telegram_schedule", AsyncMock())
    monkeypatch.setattr("bot.services.reminder_create.log_reminder_event", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.log_reminder_event", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.cancel_reminder_job", lambda *_: None)
    monkeypatch.setattr("bot.handlers.callbacks.teardown_reminder_schedule", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.cancel_reminder_telegram_schedule", AsyncMock())
    monkeypatch.setattr("bot.handlers.callbacks.menu_keyboard_for_chat", lambda _chat_id: None)
    monkeypatch.setattr("bot.handlers.callbacks.safe_callback_answer", AsyncMock())
    return scheduled


def patch_create_flow(monkeypatch) -> None:
    monkeypatch.setattr(
        "bot.handlers.create.resolve_mention_user_id",
        AsyncMock(return_value=None),
    )
