from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from bot.config import settings
from bot.db.models import Reminder, User
from bot.db.repository import async_session, get_all_active_reminders
from bot.services.admin_access import is_bot_admin
from bot.services.auto_update import force_update, schedule_process_restart
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.deploy_info import format_deploy_line
from bot.services.media import describe_stt_backends, is_ffmpeg_available
from bot.services.runtime import format_uptime, uptime_seconds
from bot.services.bot_privacy import format_group_privacy_status
from bot.services.scheduler import count_scheduled_reminder_jobs
from bot.version import __version__

router = Router()


@router.message(Command("sysinfo"))
async def cmd_sysinfo(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    me = await bot.get_me()
    privacy_line = format_group_privacy_status(
        can_read_all_group_messages=me.can_read_all_group_messages,
    )

    async with async_session() as session:
        users_count = (await session.execute(select(func.count()).select_from(User))).scalar_one()
        reminders_total = (await session.execute(select(func.count()).select_from(Reminder))).scalar_one()
        reminders_active = len(await get_all_active_reminders(session))

    ffmpeg_ok = is_ffmpeg_available()
    stt_chain = describe_stt_backends()
    sha_line = await format_deploy_line()

    await message.answer(
        "🛠 <b>Системная статистика</b>\n\n"
        f"Версия: <b>{__version__}</b>\n"
        f"{sha_line}"
        f"Аптайм: <b>{format_uptime(uptime_seconds())}</b>\n"
        f"Пользователей: <b>{users_count}</b>\n"
        f"Напоминаний всего: <b>{reminders_total}</b>\n"
        f"Активных: <b>{reminders_active}</b>\n"
        f"Задач в планировщике: <b>{count_scheduled_reminder_jobs()}</b>\n"
        f"{privacy_line}\n\n"
        f"ffmpeg: <b>{'да' if ffmpeg_ok else 'нет'}</b>\n"
        f"STT: <code>{stt_chain}</code>"
    )


@router.message(Command("setavatar"))
async def cmd_setavatar(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer("Команда доступна только админам.")
        return

    await message.answer("⏳ Загружаю аватар...")
    try:
        await ensure_bot_avatar(bot, force=True)
        await message.answer("✅ Аватар обновлён. Проверь профиль бота.")
    except Exception as exc:
        await message.answer(f"❌ Не удалось: {exc}")


@router.message(Command("grantpro"))
async def cmd_grantpro(message: Message) -> None:
    from bot.services.subscription import monetization_active

    if not monetization_active():
        await message.answer("⭐ Pro пока отключён — монетизация в разработке.")
        return

    if not is_bot_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: <code>/grantpro TELEGRAM_ID</code>")
        return

    try:
        target_id = int(parts[1].strip())
    except ValueError:
        await message.answer("Некорректный id.")
        return

    from bot.db.repository import get_or_create_user, set_user_pro

    async with async_session() as session:
        await get_or_create_user(session, target_id, settings.default_timezone)
        user = await set_user_pro(session, target_id, is_pro=True)

    if user is None:
        await message.answer("Пользователь не найден.")
        return
    await message.answer(f"⭐ Pro выдан пользователю <code>{target_id}</code>.")


@router.message(Command("update"))
async def cmd_update(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    from bot.services.deploy_meta import read_deploy_sha

    await message.answer("⏳ Проверяю обновления на GitHub…")
    local_before = read_deploy_sha()
    ok, text, new_sha = await force_update()
    await message.answer(text)
    if ok and new_sha and new_sha != local_before:
        schedule_process_restart()
