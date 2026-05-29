from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def setup_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="list", description="Список напоминаний"),
        BotCommand(command="menu", description="Показать кнопки"),
        BotCommand(command="timezone", description="Часовой пояс"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="ping", description="Проверка работы"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
