from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_CREATE = "➕ Создать"
BTN_LIST = "📋 Список"
BTN_DIARY = "📔 Дневник"
BTN_STATS = "📊 Статистика"
BTN_MORE = "⋯ Ещё"
BTN_SEARCH = "🔍 Поиск"
BTN_STATUS = "📊 Статус"
BTN_EXAMPLES = "💡 Примеры"
BTN_TIMEZONE = "🕐 Часовой пояс"
BTN_HELP = "❓ Помощь"
BTN_SETTINGS = "⚙️ Настройки"

MENU_BUTTON_TEXTS = frozenset({
    BTN_CREATE,
    BTN_LIST,
    BTN_DIARY,
    BTN_STATS,
    BTN_MORE,
    BTN_SEARCH,
    BTN_STATUS,
    BTN_EXAMPLES,
    BTN_TIMEZONE,
    BTN_HELP,
    BTN_SETTINGS,
})


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE), KeyboardButton(text=BTN_LIST)],
            [KeyboardButton(text=BTN_DIARY), KeyboardButton(text=BTN_STATS)],
            [KeyboardButton(text=BTN_MORE)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Например: через 3-4 часа созвон…",
        is_persistent=True,
    )


def menu_keyboard_for_chat(chat_id: int) -> ReplyKeyboardMarkup | None:
    """В группах reply-клавиатура не нужна (и не видна без @бот)."""
    from bot.services.timezone_ctx import is_group_chat

    return None if is_group_chat(chat_id) else main_menu_keyboard()
