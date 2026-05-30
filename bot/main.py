import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import settings
from bot.db.repository import dispose_engine, init_db
from bot.handlers import (
    admin,
    callbacks,
    create,
    edit,
    group,
    health,
    list_callbacks,
    list_cmd,
    manage,
    menu,
    search,
    start,
    status,
)
from bot.logging_setup import setup_logging
from bot.services.backup import backup_database
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.bot_menu import setup_bot_commands, setup_bot_profile
from bot.services.cleanup import prune_all_caches
from bot.services.scheduler import restore_scheduled_reminders, scheduler
from bot.version import __version__

logger = logging.getLogger(__name__)


def _acquire_instance_lock(data_dir: Path) -> Path:
    lock_path = data_dir / "bot.lock"
    if lock_path.exists():
        old_pid = lock_path.read_text(encoding="utf-8").strip()
        logger.warning("Lock file exists (pid %s) — возможен второй экземпляр бота", old_pid)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    return lock_path


def _release_instance_lock(lock_path: Path) -> None:
    try:
        if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == str(os.getpid()):
            lock_path.unlink()
    except OSError as exc:
        logger.warning("Cannot remove lock file: %s", exc)


async def _notify_admins(bot: Bot, text: str) -> None:
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.warning("Cannot notify admin %s: %s", admin_id, exc)


async def _run_backup_job() -> None:
    await asyncio.to_thread(backup_database)


async def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    lock_path = _acquire_instance_lock(data_dir)

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

    logger.info("Starting bot v%s (pid %s)", __version__, os.getpid())
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
    dp.include_router(status.router)
    dp.include_router(manage.router)
    dp.include_router(list_cmd.router)
    dp.include_router(list_callbacks.router)
    dp.include_router(search.router)
    dp.include_router(health.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    dp.include_router(edit.router)
    dp.include_router(create.router)

    scheduler.start()
    scheduler.add_job(
        prune_all_caches,
        trigger=IntervalTrigger(minutes=15),
        id="cache_cleanup",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_backup_job,
        trigger=IntervalTrigger(hours=settings.db_backup_interval_hours),
        id="db_backup",
        replace_existing=True,
    )
    await restore_scheduled_reminders(bot)
    await setup_bot_commands(bot)
    await setup_bot_profile(bot)

    try:
        await ensure_bot_avatar(bot)
    except Exception as exc:
        logger.warning("Avatar upload on startup failed: %s", exc)

    if settings.admin_telegram_ids:
        await _notify_admins(bot, f"✅ Бот запущен · v{__version__}")

    logger.info("Bot started v%s", __version__)
    try:
        await dp.start_polling(bot, handle_signals=(sys.platform != "win32"))
    except Exception:
        logger.exception("Bot stopped due to error")
        await _notify_admins(bot, "❗️ Бот упал. Смотри логи в data/logs/bot.log")
        raise
    finally:
        logger.info("Shutting down gracefully")
        if settings.admin_telegram_ids:
            try:
                await _notify_admins(bot, f"⏹ Бот останавливается · v{__version__}")
            except Exception:
                pass
        scheduler.shutdown(wait=True)
        await bot.session.close()
        await dispose_engine()
        _release_instance_lock(lock_path)


if __name__ == "__main__":
    asyncio.run(main())
