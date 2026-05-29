from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.services.reminders_ui import edit_list_message

router = Router()


@router.callback_query(F.data.startswith("list:page:"))
async def list_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[-1])
    await edit_list_message(callback, page)
    await callback.answer()


@router.callback_query(F.data == "list:noop")
async def list_noop(callback: CallbackQuery) -> None:
    await callback.answer()
