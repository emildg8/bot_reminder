from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.services.reminder_history import build_journal_message, build_stats_message
from bot.services.reminders_ui import send_active_reminders
from bot.services.timezone_ctx import get_effective_timezone

router = Router()


async def _send_journal(message: Message) -> None:
    tz = await _tz(message)
    text = await build_journal_message(message.chat.id, message.from_user.id, tz)
    await message.answer(text)


async def _send_stats(message: Message) -> None:
    tz = await _tz(message)
    text = await build_stats_message(message.chat.id, message.from_user.id, tz)
    await message.answer(text)


async def _tz(message: Message) -> str:
    from bot.db.repository import async_session

    async with async_session() as session:
        return await get_effective_timezone(session, message.chat.id, message.from_user.id)


@router.message(Command("journal"))
@router.message(Command("diary"))
async def cmd_journal(message: Message) -> None:
    await _send_journal(message)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    await _send_stats(message)


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    await send_active_reminders(message, tab="history")


@router.callback_query(F.data == "menu:diary")
async def menu_diary(callback: CallbackQuery) -> None:
    tz = await _tz(callback.message)
    text = await build_journal_message(callback.message.chat.id, callback.from_user.id, tz)
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def menu_stats(callback: CallbackQuery) -> None:
    tz = await _tz(callback.message)
    text = await build_stats_message(callback.message.chat.id, callback.from_user.id, tz)
    await callback.message.answer(text)
    await callback.answer()
