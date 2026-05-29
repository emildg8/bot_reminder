import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.db.repository import init_db
from bot.handlers import admin, callbacks, create, health, list_cmd, start
from bot.logging_setup import setup_logging
from bot.services.scheduler import restore_scheduled_reminders, scheduler

logger = logging.getLogger(__name__)


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

    logger.info("Log file: %s", log_file)
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(list_cmd.router)
    dp.include_router(health.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    dp.include_router(create.router)

    scheduler.start()
    await restore_scheduled_reminders(bot)

    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    except Exception:
        logger.exception("Bot stopped due to error")
        if settings.admin_telegram_ids:
            for admin_id in settings.admin_telegram_ids:
                try:
                    await bot.send_message(admin_id, "❗️Бот упал. Смотри логи в data/logs/bot.log")
                except Exception:
                    pass
        raise
    finally:
        logger.info("Shutting down")
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
