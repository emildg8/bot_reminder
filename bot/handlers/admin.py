from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from bot.db.models import Reminder, User
from bot.db.repository import async_session, get_all_active_reminders
from bot.keyboards.reply import (
    ADMIN_MODE_BUTTON_TEXTS,
    menu_keyboard_for_chat,
    menu_keyboard_for_user,
)
from bot.services.admin_access import (
    format_bot_admin_denied,
    is_admin_listed,
    is_bot_admin,
)
from bot.services.admin_mode import (
    admin_mode_keyboard,
    apply_admin_mode,
    toggle_admin_mode,
)
from bot.services.admin_audit import format_admin_log, log_admin_action
from bot.services.admin_panel import (
    BROADCAST_HELP,
    BroadcastFilter,
    PendingBroadcast,
    admin_limited_keyboard,
    admin_panel_keyboard,
    broadcast_message,
    broadcast_preview_keyboard,
    build_userinfo_reply,
    count_broadcast_recipients,
    fetch_recent_users,
    format_admin_panel_intro,
    format_admin_panel_limited,
    format_admin_stats,
    format_admins_list,
    format_broadcast_preview,
    format_recent_users,
    format_user_reminders,
    format_userfind_results,
    get_pending_broadcast,
    is_userinfo_card,
    notify_other_admins,
    parse_broadcast_message,
    parse_target_telegram_id,
    pop_pending_broadcast,
    recent_users_keyboard,
    send_broadcast_preview_to_admin,
    set_pending_broadcast,
)
from bot.services.auto_update import force_update, schedule_process_restart
from bot.services.bot_avatar import ensure_bot_avatar
from bot.services.deploy_info import format_deploy_line
from bot.services.media import describe_stt_backends, is_ffmpeg_available
from bot.services.runtime import format_uptime, uptime_seconds
from bot.services.bot_privacy import format_group_privacy_status
from bot.services.scheduler import count_scheduled_reminder_jobs
from bot.texts.messages import format_admin_mode_ack, format_admin_mode_status
from bot.version import __version__

router = Router()


def _callback_target_id(callback: CallbackQuery) -> int | None:
    try:
        return int((callback.data or "").split(":")[-1])
    except ValueError:
        return None


async def _deny_admin(message: Message) -> None:
    await message.answer(format_bot_admin_denied(message.from_user.id))


async def _reply_userinfo(message: Message, target_id: int, *, edit: bool = False) -> None:
    text, kb = await build_userinfo_reply(target_id)
    kwargs = {"reply_markup": kb} if kb else {}
    if edit:
        await message.edit_text(text, **kwargs)
    else:
        await message.answer(text, **kwargs)


async def _finish_broadcast(
    bot: Bot,
    admin_id: int,
    pending: PendingBroadcast,
    delivered: int,
    failed: int,
    total: int,
) -> str:
    label = pending.filter.value
    summary = (
        f"📢 рассылка ({label}): доставлено {delivered}/{total}, ошибок {failed}"
    )
    await log_admin_action(admin_id, summary)
    await notify_other_admins(
        bot,
        admin_id,
        f"📢 <b>Рассылка</b> от <code>{admin_id}</code>\n"
        f"Аудитория: <b>{label}</b> · доставлено <b>{delivered}</b>/{total}",
    )
    return (
        f"📢 <b>Рассылка завершена</b> ({label})\n"
        f"Попыток: <b>{total}</b>\n"
        f"Доставлено: <b>{delivered}</b>\n"
        f"Ошибок: <b>{failed}</b>"
    )


async def _reply_mode_change(
    target: Message,
    bot: Bot,
    *,
    admin_tools: bool,
    full_status: bool = False,
) -> None:
    text = format_admin_mode_status(admin_tools=admin_tools) if full_status else format_admin_mode_ack(
        admin_tools=admin_tools
    )
    await target.answer(
        text,
        reply_markup=admin_mode_keyboard(admin_tools=admin_tools),
    )
    if target.chat.id > 0:
        await target.answer(
            "⌨️ Меню обновлено под режим.",
            reply_markup=menu_keyboard_for_user(target.from_user.id),
        )


@router.message(Command("adminmode"))
async def cmd_adminmode(message: Message, bot: Bot) -> None:
    if not is_admin_listed(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 1:
        admin_tools = is_bot_admin(message.from_user.id)
        await _reply_mode_change(message, bot, admin_tools=admin_tools, full_status=True)
        return

    mode = parts[1].strip().lower()
    if mode in ("admin", "adm", "админ", "a", "on", "1"):
        admin_tools = True
    elif mode in ("user", "usr", "пользователь", "юзер", "u", "off", "0"):
        admin_tools = False
    elif mode in ("toggle", "switch", "переключить"):
        admin_tools, _ = await toggle_admin_mode(bot, message.from_user.id)
        await _reply_mode_change(message, bot, admin_tools=admin_tools)
        return
    else:
        await message.answer(
            "Формат:\n"
            "• <code>/adminmode</code> — статус\n"
            "• <code>/adminmode admin</code> · <code>user</code>\n"
            "• <code>/adminmode toggle</code>\n"
            "• Кнопка внизу экрана «👤 Как пользователь» / «🛠 Режим админа»"
        )
        return

    if admin_tools == is_bot_admin(message.from_user.id):
        await message.answer(
            format_admin_mode_status(admin_tools=admin_tools),
            reply_markup=admin_mode_keyboard(admin_tools=admin_tools),
        )
        return

    await apply_admin_mode(bot, message.from_user.id, admin_tools=admin_tools)
    await _reply_mode_change(message, bot, admin_tools=admin_tools)


@router.message(F.text.in_(ADMIN_MODE_BUTTON_TEXTS))
async def btn_admin_mode(message: Message, bot: Bot) -> None:
    if not is_admin_listed(message.from_user.id):
        return
    admin_tools, _ = await toggle_admin_mode(bot, message.from_user.id)
    await _reply_mode_change(message, bot, admin_tools=admin_tools)


@router.callback_query(F.data.in_({"adminmode:admin", "adminmode:user"}))
async def cb_adminmode(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin_listed(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return

    admin_tools = callback.data == "adminmode:admin"
    if admin_tools == is_bot_admin(callback.from_user.id):
        await callback.answer("Уже выбран этот режим")
        return

    await apply_admin_mode(bot, callback.from_user.id, admin_tools=admin_tools)
    text = format_admin_mode_status(admin_tools=admin_tools)
    await callback.message.edit_text(
        text,
        reply_markup=admin_mode_keyboard(admin_tools=admin_tools),
    )
    label = "администратора" if admin_tools else "пользователя"
    await callback.answer(f"Режим: {label}")
    if callback.message.chat.id > 0:
        await callback.message.answer(
            "⌨️ Меню обновлено.",
            reply_markup=menu_keyboard_for_user(callback.from_user.id),
        )


@router.message(Command("admin"))
async def cmd_admin_panel(message: Message) -> None:
    if not is_admin_listed(message.from_user.id):
        await message.answer("Команда доступна только администраторам бота.")
        return
    if not is_bot_admin(message.from_user.id):
        await message.answer(
            format_admin_panel_limited(),
            reply_markup=admin_limited_keyboard(),
        )
        return
    await message.answer(
        await format_admin_panel_intro(),
        reply_markup=admin_panel_keyboard(),
    )


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return
    target_id = parse_target_telegram_id(message)
    if target_id is None:
        await message.answer(
            "Формат: <code>/userinfo TELEGRAM_ID</code>\n"
            "Или <b>ответь</b> на сообщение человека и отправь <code>/userinfo</code>"
        )
        return
    await _reply_userinfo(message, target_id)


@router.message(Command("adminlog"))
async def cmd_adminlog(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return
    await message.answer(await format_admin_log())


@router.message(Command("adminstats"))
async def cmd_adminstats(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return
    await message.answer(await format_admin_stats())


@router.message(Command("userfind"))
async def cmd_userfind(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Формат: <code>/userfind 123456</code>\n"
            "Минимум 3 цифры — поиск по фрагменту Telegram ID."
        )
        return
    text, kb = await format_userfind_results(parts[1].strip())
    await message.answer(text, reply_markup=kb)


@router.message(Command("admins"))
async def cmd_admins(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return
    await message.answer(await format_admins_list(message.from_user.id))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await _deny_admin(message)
        return

    parsed = parse_broadcast_message(message)
    if parsed is None or parsed.action == "help":
        await message.answer(BROADCAST_HELP)
        return

    if parsed.action == "test":
        ok = await send_broadcast_preview_to_admin(bot, message.from_user.id, parsed.text)
        await message.answer(
            "📨 Пример отправлен тебе в личку." if ok else "❌ Не удалось отправить пример."
        )
        return

    if parsed.action == "send":
        await message.answer("⏳ Рассылка…")
        delivered, failed, total = await broadcast_message(
            bot, parsed.text, filter=parsed.filter
        )
        pending = PendingBroadcast(text=parsed.text, filter=parsed.filter)
        await message.answer(
            await _finish_broadcast(
                bot, message.from_user.id, pending, delivered, failed, total
            )
        )
        return

    total_users = await count_broadcast_recipients(parsed.filter)
    await set_pending_broadcast(message.from_user.id, parsed.text, filter=parsed.filter)
    await message.answer(
        format_broadcast_preview(parsed.text, total_users, filter=parsed.filter),
        reply_markup=broadcast_preview_keyboard(current=parsed.filter),
    )


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery) -> None:
    if not is_admin_listed(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    if not is_bot_admin(callback.from_user.id):
        await callback.message.edit_text(
            format_admin_panel_limited(),
            reply_markup=admin_limited_keyboard(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        await format_admin_panel_intro(),
        reply_markup=admin_panel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:hint:"))
async def cb_admin_hint(callback: CallbackQuery) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    hint = (callback.data or "").removeprefix("admin:hint:")
    if hint == "userinfo":
        msg = "/userinfo ID или ответ + /userinfo"
    elif hint == "broadcast":
        msg = "/broadcast [активные|pro|free] текст"
    elif hint == "find":
        msg = "/userfind 123456 — поиск ID"
    else:
        msg = "—"
    await callback.answer(msg, show_alert=True)


@router.callback_query(F.data.startswith("admin:userinfo:"))
async def cb_admin_userinfo(callback: CallbackQuery) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    target_id = _callback_target_id(callback)
    if target_id is None:
        await callback.answer("Ошибка id", show_alert=True)
        return
    await callback.answer()
    body = callback.message.text or callback.message.caption or ""
    await _reply_userinfo(callback.message, target_id, edit=is_userinfo_card(body))


@router.callback_query(F.data.startswith("admin:reminders:"))
async def cb_admin_reminders(callback: CallbackQuery) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    target_id = _callback_target_id(callback)
    await callback.answer()
    await callback.message.answer(await format_user_reminders(target_id))


@router.callback_query(F.data.startswith("admin:bcast:filter:"))
async def cb_broadcast_filter(callback: CallbackQuery) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    pending = await get_pending_broadcast(callback.from_user.id)
    if pending is None:
        await callback.answer("Сначала /broadcast текст", show_alert=True)
        return
    try:
        filt = BroadcastFilter((callback.data or "").split(":")[-1])
    except ValueError:
        await callback.answer("Неизвестный фильтр", show_alert=True)
        return
    await set_pending_broadcast(callback.from_user.id, pending.text, filter=filt)
    total = await count_broadcast_recipients(filt)
    await callback.message.edit_text(
        format_broadcast_preview(pending.text, total, filter=filt),
        reply_markup=broadcast_preview_keyboard(current=filt),
    )
    await callback.answer(f"Фильтр: {filt.value}")


@router.callback_query(F.data == "admin:bcast:self")
async def cb_broadcast_self(callback: CallbackQuery, bot: Bot) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    pending = await get_pending_broadcast(callback.from_user.id)
    if pending is None:
        await callback.answer("Нет черновика", show_alert=True)
        return
    ok = await send_broadcast_preview_to_admin(bot, callback.from_user.id, pending.text)
    await callback.answer("Отправлено тебе" if ok else "Ошибка отправки", show_alert=not ok)


@router.callback_query(F.data.in_({"admin:bcast:confirm", "admin:bcast:cancel"}))
async def cb_broadcast_confirm(callback: CallbackQuery, bot: Bot) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    if callback.data == "admin:bcast:cancel":
        await pop_pending_broadcast(callback.from_user.id)
        await callback.message.edit_text("❌ Рассылка отменена.")
        await callback.answer()
        return
    pending = await pop_pending_broadcast(callback.from_user.id)
    if pending is None:
        await callback.answer("Текст устарел — создай /broadcast заново", show_alert=True)
        return
    await callback.answer("Отправляю…")
    await callback.message.edit_text("⏳ Рассылка…")
    delivered, failed, total = await broadcast_message(
        bot, pending.text, filter=pending.filter
    )
    await callback.message.edit_text(
        await _finish_broadcast(
            bot, callback.from_user.id, pending, delivered, failed, total
        )
    )


@router.callback_query(F.data.startswith("admin:run:"))
async def cb_admin_run(callback: CallbackQuery, bot: Bot) -> None:
    if not is_admin_listed(callback.from_user.id):
        await callback.answer("Недоступно", show_alert=True)
        return
    action = (callback.data or "").removeprefix("admin:run:")
    if action != "adminmode" and not is_bot_admin(callback.from_user.id):
        await callback.answer(format_bot_admin_denied(callback.from_user.id), show_alert=True)
        return
    await callback.answer()
    if action == "admins":
        await callback.message.answer(await format_admins_list(callback.from_user.id))
    elif action == "recent":
        rows = await fetch_recent_users()
        await callback.message.answer(
            await format_recent_users(),
            reply_markup=recent_users_keyboard(rows) if rows else None,
        )
    elif action == "stats":
        await callback.message.answer(await format_admin_stats())
    elif action == "log":
        await callback.message.answer(await format_admin_log())
    elif action == "adminmode":
        await cmd_adminmode(callback.message, bot)


@router.callback_query(F.data.startswith("adminmode:cmd:"))
async def cb_adminmode_run_cmd(callback: CallbackQuery, bot: Bot) -> None:
    if not is_bot_admin(callback.from_user.id):
        await callback.answer(format_bot_admin_denied(callback.from_user.id), show_alert=True)
        return

    cmd = (callback.data or "").removeprefix("adminmode:cmd:")
    await callback.answer()
    if cmd == "health":
        from bot.handlers.health import cmd_health

        await cmd_health(callback.message, bot)
    elif cmd == "sysinfo":
        await cmd_sysinfo(callback.message, bot)
    elif cmd == "update":
        await cmd_update(callback.message)


@router.message(Command("sysinfo"))
async def cmd_sysinfo(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer(format_bot_admin_denied(message.from_user.id))
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
    mode_line = "🛠 admin-tools: <b>вкл</b>"

    await message.answer(
        "🛠 <b>Системная статистика</b>\n\n"
        f"Версия: <b>{__version__}</b>\n"
        f"{sha_line}"
        f"Аптайм: <b>{format_uptime(uptime_seconds())}</b>\n"
        f"{mode_line}\n"
        f"Пользователей: <b>{users_count}</b>\n"
        f"Напоминаний всего: <b>{reminders_total}</b>\n"
        f"Активных: <b>{reminders_active}</b>\n"
        f"Задач в планировщике: <b>{count_scheduled_reminder_jobs()}</b>\n"
        f"{privacy_line}\n\n"
        f"ffmpeg: <b>{'да' if ffmpeg_ok else 'нет'}</b>\n"
        f"STT: <code>{stt_chain}</code>",
        reply_markup=menu_keyboard_for_chat(message.chat.id, message.from_user.id),
    )


@router.message(Command("setavatar"))
async def cmd_setavatar(message: Message, bot: Bot) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer(format_bot_admin_denied(message.from_user.id))
        return

    await message.answer("⏳ Загружаю аватар...")
    try:
        await ensure_bot_avatar(bot, force=True)
        await message.answer("✅ Аватар обновлён. Проверь профиль бота.")
    except Exception as exc:
        await message.answer(f"❌ Не удалось: {exc}")


@router.message(Command("update"))
async def cmd_update(message: Message) -> None:
    if not is_bot_admin(message.from_user.id):
        await message.answer(format_bot_admin_denied(message.from_user.id))
        return

    from bot.services.deploy_meta import read_deploy_sha

    await message.answer("⏳ Проверяю обновления на GitHub…")
    local_before = read_deploy_sha()
    ok, text, new_sha = await force_update()
    await message.answer(text)
    if ok and new_sha and new_sha != local_before:
        schedule_process_restart()
