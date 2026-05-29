from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

_started_at = datetime.now(timezone.utc)

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    uptime = datetime.now(timezone.utc) - _started_at
    secs = int(uptime.total_seconds())
    await message.answer(f"✅ ok (uptime {secs}s)")

