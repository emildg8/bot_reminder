from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.reminders_ui import send_active_reminders

router = Router()


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    await send_active_reminders(message)
