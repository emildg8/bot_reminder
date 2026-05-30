from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_CREATE = "➕ Создать"
BTN_LIST = "📋 Список"
BTN_SEARCH = "🔍 Поиск"
BTN_STATUS = "📊 Статус"
BTN_EXAMPLES = "💡 Примеры"
BTN_TIMEZONE = "🕐 Часовой пояс"
BTN_HELP = "❓ Помощь"

MENU_BUTTON_TEXTS = frozenset({
    BTN_CREATE,
    BTN_LIST,
    BTN_SEARCH,
    BTN_STATUS,
    BTN_EXAMPLES,
    BTN_TIMEZONE,
    BTN_HELP,
})


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE), KeyboardButton(text=BTN_LIST), KeyboardButton(text=BTN_SEARCH)],
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_EXAMPLES)],
            [KeyboardButton(text=BTN_TIMEZONE), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Например: через 1 час созвон…",
        is_persistent=True,
    )
