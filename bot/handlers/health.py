from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.admin_access import is_bot_admin
from bot.services.deploy_info import format_deploy_line
from bot.services.health_status import format_health_message, run_health_check
from bot.services.runtime import format_uptime, uptime_seconds
from bot.version import __version__

router = Router()


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    uptime = format_uptime(uptime_seconds())
    await message.answer(f"✅ Бот работает · v{__version__} · аптайм {uptime}")


@router.message(Command("health"))
async def cmd_health(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    snapshot, repair = await run_health_check(bot)
    deploy_line = await format_deploy_line()
    text = format_health_message(
        snapshot,
        version=__version__,
        uptime=format_uptime(uptime_seconds()),
        deploy_line=deploy_line,
        repair=repair,
    )
    await message.answer(text)
