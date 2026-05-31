from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from bot.config import settings


PRIVATE_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="list", description="Активные напоминания"),
    BotCommand(command="history", description="История за сегодня"),
    BotCommand(command="journal", description="Дневник дня"),
    BotCommand(command="stats", description="Статистика за месяц"),
    BotCommand(command="settings", description="Настройки отложить"),
    BotCommand(command="status", description="Статус"),
    BotCommand(command="search", description="Поиск по тексту"),
    BotCommand(command="cancel", description="Отменить режим"),
    BotCommand(command="edit", description="Изменить напоминание"),
    BotCommand(command="menu", description="Показать кнопки"),
    BotCommand(command="timezone", description="Часовой пояс"),
    BotCommand(command="export", description="Экспорт в JSON"),
    BotCommand(command="import", description="Импорт из JSON"),
    BotCommand(command="about", description="О боте"),
    BotCommand(command="help", description="Справка"),
    BotCommand(command="ping", description="Проверка работы"),
]

COLLECTIVE_COMMANDS = [
    BotCommand(command="remind", description="Создать напоминание"),
    BotCommand(command="list", description="Активные напоминания"),
    BotCommand(command="edit", description="Изменить напоминание"),
    BotCommand(command="pause", description="Пауза"),
    BotCommand(command="resume", description="Возобновить"),
    BotCommand(command="timezone", description="Часовой пояс чата"),
    BotCommand(command="status", description="Статус чата"),
    BotCommand(command="clear", description="Удалить все в чате"),
    BotCommand(command="help", description="Справка"),
    BotCommand(command="ping", description="Проверка"),
]

CHANNEL_COMMANDS = [
    BotCommand(command="remind", description="Напоминание в канале"),
    BotCommand(command="list", description="Активные"),
    BotCommand(command="pause", description="Пауза"),
    BotCommand(command="resume", description="Возобновить"),
    BotCommand(command="timezone", description="Часовой пояс"),
    BotCommand(command="status", description="Статус"),
    BotCommand(command="help", description="Справка"),
]


async def setup_bot_commands(bot: Bot) -> None:
    commands = list(PRIVATE_COMMANDS)
    if settings.admin_telegram_ids:
        commands.append(
            BotCommand(command="sysinfo", description="Системная статистика (админ)")
        )
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    await bot.set_my_commands(COLLECTIVE_COMMANDS, scope=BotCommandScopeAllGroupChats())


async def setup_channel_commands(bot: Bot, chat_id: int) -> None:
    await bot.set_my_commands(CHANNEL_COMMANDS, scope=BotCommandScopeChat(chat_id=chat_id))


async def setup_bot_profile(bot: Bot) -> None:
    await bot.set_my_description(settings.bot_description)
    await bot.set_my_short_description(settings.bot_short_description)
