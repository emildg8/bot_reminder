from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="list", description="Список напоминаний"),
        BotCommand(command="edit", description="Изменить напоминание"),
        BotCommand(command="menu", description="Показать кнопки"),
        BotCommand(command="timezone", description="Часовой пояс"),
        BotCommand(command="clear", description="Удалить все напоминания"),
        BotCommand(command="export", description="Экспорт в JSON"),
        BotCommand(command="import", description="Импорт из JSON"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="ping", description="Проверка работы"),
        BotCommand(command="health", description="Health (админ)"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
