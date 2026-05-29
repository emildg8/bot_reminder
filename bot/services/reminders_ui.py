from aiogram.types import Message

from bot.config import settings
from bot.db.repository import async_session, get_active_chat_reminders, get_or_create_user
from bot.keyboards.inline import list_manage_keyboard
from bot.services.reminder_display import format_reminder_list_line


async def send_active_reminders(message: Message) -> None:
    viewer_id = message.from_user.id
    async with async_session() as session:
        await get_or_create_user(
            session,
            telegram_id=viewer_id,
            timezone=settings.default_timezone,
        )
        reminders = await get_active_chat_reminders(session, message.chat.id)

    if not reminders:
        await message.answer("Активных напоминаний нет.")
        return

    lines = [format_reminder_list_line(r, r.timezone) for r in reminders]
    body = f"<b>Активных напоминаний: {len(reminders)}</b>\n\n" + "\n".join(lines)
    keyboard = list_manage_keyboard(reminders, viewer_id)

    hint = ""
    if message.chat.id < 0:
        hint = "\n\n<i>Кнопки ✏️/🗑 — только для твоих напоминаний.</i>"

    await message.answer(body + hint, reply_markup=keyboard)
