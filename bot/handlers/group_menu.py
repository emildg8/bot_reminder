from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.services.group_menu import dismiss_legacy_group_menu
from bot.services.reminders_ui import send_active_reminders
from bot.services.callback_utils import safe_callback_answer

router = Router()


@router.callback_query(F.data.startswith("gmenu:"))
async def gmenu_legacy(callback: CallbackQuery) -> None:
    if callback.data == "gmenu:list":
        await safe_callback_answer(callback)
        await send_active_reminders(callback.message)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return
    await dismiss_legacy_group_menu(callback)
