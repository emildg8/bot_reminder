from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_LIST = "📋 Список"
BTN_CREATE = "➕ Создать"
BTN_TIMEZONE = "🕐 Часовой пояс"
BTN_HELP = "❓ Помощь"
BTN_EXAMPLES = "💡 Примеры"

MENU_BUTTON_TEXTS = frozenset({BTN_LIST, BTN_CREATE, BTN_TIMEZONE, BTN_HELP, BTN_EXAMPLES})


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE), KeyboardButton(text=BTN_LIST)],
            [KeyboardButton(text=BTN_TIMEZONE), KeyboardButton(text=BTN_HELP)],
            [KeyboardButton(text=BTN_EXAMPLES)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напомни через час…",
    )
