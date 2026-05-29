from zoneinfo import ZoneInfo

from aiogram.types import Message

from bot.config import settings
from bot.db.repository import async_session, get_active_chat_reminders, get_or_create_user
from bot.keyboards.inline import list_reminder_keyboard


def _format_list_item(reminder, timezone: str) -> str:
    tz = ZoneInfo(timezone)
    if reminder.next_run_at:
        when = reminder.next_run_at.astimezone(tz).strftime("%d.%m %H:%M")
    elif reminder.daily_time:
        when = f"ежедневно {reminder.daily_time.strftime('%H:%M')}"
    else:
        when = "—"

    kind_labels = {
        "once": "разово",
        "interval": "интервал",
        "daily": "ежедневно",
        "weekly": "по дням недели",
    }
    kind = kind_labels.get(reminder.kind, reminder.kind)
    return f"#{reminder.id} [{kind}] {when} — {reminder.text}"


async def send_active_reminders(message: Message) -> None:
    async with async_session() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            timezone=settings.default_timezone,
        )
        reminders = await get_active_chat_reminders(session, message.chat.id)

    if not reminders:
        await message.answer("Активных напоминаний нет.")
        return

    await message.answer(f"Активных напоминаний: {len(reminders)}")
    for reminder in reminders:
        text = _format_list_item(reminder, reminder.timezone)
        await message.answer(text, reply_markup=list_reminder_keyboard(reminder.id))
