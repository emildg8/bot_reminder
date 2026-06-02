"""Режим admin / user для администраторов бота."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.db.repository import async_session
from bot.services.admin_access import (
    get_admin_tools_enabled,
    is_admin_listed,
    is_bot_admin,
    set_admin_tools_enabled,
)
from bot.services.bot_menu import PRIVATE_COMMANDS
from bot.texts.messages import format_admin_mode_status

ADMIN_EXTRA_COMMANDS = [
    BotCommand(command="admin", description="Панель администратора"),
    BotCommand(command="health", description="Диагностика (админ)"),
    BotCommand(command="sysinfo", description="Системная статистика (админ)"),
    BotCommand(command="userinfo", description="Карточка пользователя (админ)"),
    BotCommand(command="admins", description="Список админов бота"),
    BotCommand(command="update", description="Обновить с GitHub (админ)"),
    BotCommand(command="setavatar", description="Аватар бота (админ)"),
    BotCommand(command="adminlog", description="Журнал админ-действий"),
]

ADMIN_MODE_COMMAND = BotCommand(command="adminmode", description="Режим: admin / user")


def admin_mode_keyboard(*, admin_tools: bool) -> InlineKeyboardMarkup:
    if admin_tools:
        toggle = InlineKeyboardButton(
            text="👤 Режим пользователя",
            callback_data="adminmode:user",
        )
        quick = [
            InlineKeyboardButton(text="🏥 Health", callback_data="adminmode:cmd:health"),
            InlineKeyboardButton(text="📈 Sysinfo", callback_data="adminmode:cmd:sysinfo"),
        ]
    else:
        toggle = InlineKeyboardButton(
            text="🛠 Режим администратора",
            callback_data="adminmode:admin",
        )
        quick = []

    rows: list[list[InlineKeyboardButton]] = [[toggle]]
    if quick:
        rows.append(quick)
    rows.append(
        [
            InlineKeyboardButton(text="🎛 Панель", callback_data="admin:panel"),
            InlineKeyboardButton(text="📊 Статус", callback_data="menu:status"),
        ]
    )
    rows.append([InlineKeyboardButton(text="❓ Справка", callback_data="menu:help")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def more_menu_admin_row(*, admin_tools: bool) -> list[InlineKeyboardButton]:
    if admin_tools:
        return [
            InlineKeyboardButton(
                text="👤 Тест как пользователь",
                callback_data="adminmode:user",
            )
        ]
    return [
        InlineKeyboardButton(
            text="🛠 Режим администратора",
            callback_data="adminmode:admin",
        )
    ]


async def sync_admin_command_menu(bot: Bot, admin_telegram_id: int, *, admin_tools: bool) -> None:
    commands = list(PRIVATE_COMMANDS)
    if admin_tools:
        commands.extend(ADMIN_EXTRA_COMMANDS)
    commands.append(ADMIN_MODE_COMMAND)
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=admin_telegram_id))


async def apply_admin_mode(bot: Bot, telegram_id: int, *, admin_tools: bool) -> str:
    async with async_session() as session:
        await set_admin_tools_enabled(session, telegram_id, admin_tools)
    await sync_admin_command_menu(bot, telegram_id, admin_tools=admin_tools)
    return format_admin_mode_status(admin_tools=admin_tools)


async def toggle_admin_mode(bot: Bot, telegram_id: int) -> tuple[bool, str]:
    new_tools = not is_bot_admin(telegram_id)
    text = await apply_admin_mode(bot, telegram_id, admin_tools=new_tools)
    return new_tools, text


async def setup_all_admin_command_menus(bot: Bot) -> None:
    if not settings.admin_telegram_ids:
        return
    async with async_session() as session:
        for admin_id in settings.admin_telegram_ids:
            if not is_admin_listed(admin_id):
                continue
            enabled = await get_admin_tools_enabled(session, admin_id)
            await sync_admin_command_menu(bot, admin_id, admin_tools=enabled)
