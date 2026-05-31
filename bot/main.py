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
    diary,
    edit,
    group,
    group_menu,
    health,
    list_callbacks,
    list_cmd,
    manage,
    menu,
    search,
    settings as settings_handler,
    start,
    status,
)
from bot.logging_setup import setup_logging
from bot.services.backup import backup_database
from bot.services.media import is_ffmpeg_available
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.bot_menu import setup_bot_commands, setup_bot_profile
from bot.services.auto_update import (
    apply_git_update_to_sha,
    consume_reexec_flag,
    register_shutdown_dispatcher,
    request_process_reexec,
    should_restart_for_update,
)
from bot.services.cleanup import prune_all_caches
from bot.services.deploy_meta import record_deploy_sha_from_git
from bot.services.heartbeat import write_heartbeat
from bot.services.instance_lock import acquire_instance_lock, release_instance_lock
from bot.services.process_restart import exit_for_restart
from bot.services.scheduler import repair_reminder_jobs, restore_scheduled_reminders, scheduler
from bot.version import __version__

logger = logging.getLogger(__name__)


async def _notify_admins(bot: Bot, text: str) -> None:
    for admin_id in settings.admin_telegram_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:
            logger.warning("Cannot notify admin %s: %s", admin_id, exc)


async def _run_backup_job() -> None:
    await asyncio.to_thread(backup_database)


def _heartbeat_job() -> None:
    write_heartbeat(scheduler_running=scheduler.running)


async def _stop_polling_safe(dp: Dispatcher) -> None:
    try:
        await dp.stop_polling()
    except RuntimeError as exc:
        if "not started" not in str(exc).lower():
            raise


async def _auto_update_job(
    bot: Bot,
    dp: Dispatcher,
    *,
    polling_active: bool = True,
) -> bool:
    """Проверяет GitHub и обновляет код. True → нужен re-exec."""
    need_restart, local_sha, remote_sha = await should_restart_for_update()
    if not need_restart or not remote_sha:
        return False

    short = remote_sha[:7]
    await _notify_admins(
        bot,
        f"🔄 Новая версия на GitHub (<code>{short}</code>) — скачиваю обновление…",
    )
    logger.info("Auto-update: %s -> %s", (local_sha or "?")[:7], short)

    success, new_sha = await apply_git_update_to_sha(remote_sha)
    if not success:
        await _notify_admins(
            bot,
            f"⚠️ Не удалось обновиться до <code>{short}</code>. Проверь логи или перезапусти сервер.",
        )
        return False

    applied = (new_sha or remote_sha)[:7]
    await _notify_admins(
        bot,
        f"✅ Обновлено до <code>{applied}</code> — перезапуск процесса…",
    )
    request_process_reexec()
    if polling_active:
        await _stop_polling_safe(dp)
    return True


async def _shutdown_bot(bot: Bot, lock_path: Path) -> None:
    scheduler.shutdown(wait=True)
    await bot.session.close()
    await dispose_engine()
    release_instance_lock(lock_path)


async def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    lock_path = acquire_instance_lock(data_dir)

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
    if not is_ffmpeg_available():
        logger.warning("ffmpeg not found — локальный Whisper и кружочки без Groq могут не работать")
    else:
        logger.info("ffmpeg: available")
    logger.info("Log file: %s", log_file)
    deploy_sha = record_deploy_sha_from_git()
    if deploy_sha:
        logger.info("Deploy sha: %s", deploy_sha[:7])
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    me = await bot.get_me()
    logger.info("Bot identity: @%s (id %s)", me.username, me.id)

    webhook = await bot.get_webhook_info()
    if webhook.url:
        logger.warning("Webhook was set (%s) — switching to polling", webhook.url)
    await bot.delete_webhook(drop_pending_updates=False)

    dp = Dispatcher()
    register_shutdown_dispatcher(dp)
    dp.include_router(start.router)
    dp.include_router(group.router)
    dp.include_router(group_menu.router)
    dp.include_router(menu.router)
    dp.include_router(diary.router)
    dp.include_router(settings_handler.router)
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
    write_heartbeat(scheduler_running=True)
    scheduler.add_job(
        _heartbeat_job,
        trigger=IntervalTrigger(seconds=30),
        id="heartbeat",
        replace_existing=True,
    )
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
    scheduler.add_job(
        repair_reminder_jobs,
        trigger=IntervalTrigger(minutes=3),
        id="repair_reminders",
        replace_existing=True,
        kwargs={"bot": bot},
    )
    if settings.auto_update_enabled:
        scheduler.add_job(
            _auto_update_job,
            trigger=IntervalTrigger(minutes=settings.auto_update_interval_minutes),
            id="auto_update",
            replace_existing=True,
            kwargs={"bot": bot, "dp": dp},
        )
    await restore_scheduled_reminders(bot)
    if settings.auto_update_enabled:
        if await _auto_update_job(bot, dp, polling_active=False):
            await _shutdown_bot(bot, lock_path)
            exit_for_restart("Startup auto-update applied")
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
        await _shutdown_bot(bot, lock_path)

    if consume_reexec_flag():
        exit_for_restart("Auto-update applied")


if __name__ == "__main__":
    asyncio.run(main())
