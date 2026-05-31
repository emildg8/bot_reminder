from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import settings


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="list", description="Активные напоминания"),
        BotCommand(command="history", description="История за сегодня"),
        BotCommand(command="journal", description="Дневник дня"),
        BotCommand(command="stats", description="Статистика за месяц"),
        BotCommand(command="settings", description="Настройки отложить"),
        BotCommand(command="status", description="Статус чата"),
        BotCommand(command="search", description="Поиск по тексту"),
        BotCommand(command="cancel", description="Отменить режим"),
        BotCommand(command="edit", description="Изменить напоминание"),
        BotCommand(command="pause", description="Пауза напоминаний"),
        BotCommand(command="resume", description="Возобновить"),
        BotCommand(command="menu", description="Показать кнопки"),
        BotCommand(command="timezone", description="Часовой пояс"),
        BotCommand(command="clear", description="Удалить все напоминания"),
        BotCommand(command="export", description="Экспорт в JSON"),
        BotCommand(command="import", description="Импорт из JSON"),
        BotCommand(command="about", description="О боте"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="remind", description="Создать напоминание (группы)"),
        BotCommand(command="ping", description="Проверка работы"),
        BotCommand(command="sysinfo", description="Системная статистика (админ)"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def setup_bot_profile(bot: Bot) -> None:
    await bot.set_my_description(settings.bot_description)
    await bot.set_my_short_description(settings.bot_short_description)
