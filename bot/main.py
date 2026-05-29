import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import settings
from bot.db.repository import init_db
from bot.handlers import admin, callbacks, create, edit, group, health, list_cmd, manage, menu, start
from bot.logging_setup import setup_logging
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.bot_menu import setup_bot_commands
from bot.services.drafts import prune_expired
from bot.services.scheduler import restore_scheduled_reminders, scheduler
from bot.version import __version__

logger = logging.getLogger(__name__)


async def _notify_admins(bot: Bot, text: str) -> None:
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.warning("Cannot notify admin %s: %s", admin_id, exc)


async def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    log_file = setup_logging(
        data_dir / "logs",
        max_bytes=settings.log_max_bytes,
        backup_count=settings.log_backup_count,
    )

    loop = asyncio.get_running_loop()
    log = logging.getLogger("bot.exceptions")

    def asyncio_handler(_loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exc = context.get("exception")
        message = context.get("message", "asyncio error")
        if exc is not None:
            log.error("%s", message, exc_info=exc)
        else:
            log.error("%s — context: %s", message, context)

    loop.set_exception_handler(asyncio_handler)

    logger.info("Starting bot v%s", __version__)
    logger.info("Log file: %s", log_file)
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(group.router)
    dp.include_router(menu.router)
    dp.include_router(manage.router)
    dp.include_router(list_cmd.router)
    dp.include_router(health.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    dp.include_router(edit.router)
    dp.include_router(create.router)

    scheduler.start()
    scheduler.add_job(
        prune_expired,
        trigger=IntervalTrigger(minutes=15),
        id="draft_cleanup",
        replace_existing=True,
    )
    await restore_scheduled_reminders(bot)
    await setup_bot_commands(bot)

    try:
        await ensure_bot_avatar(bot)
    except Exception as exc:
        logger.warning("Avatar upload on startup failed: %s", exc)

    if settings.admin_telegram_ids:
        await _notify_admins(bot, f"✅ Бот запущен · v{__version__}")

    logger.info("Bot started v%s", __version__)
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot stopped due to error")
        await _notify_admins(bot, "❗️ Бот упал. Смотри логи в data/logs/bot.log")
        raise
    finally:
        logger.info("Shutting down")
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
