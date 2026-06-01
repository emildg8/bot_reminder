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
BTN_ADMIN_AS_USER = "👤 Как пользователь"
BTN_ADMIN_TOOLS = "🛠 Режим админа"

ADMIN_MODE_BUTTON_TEXTS = frozenset({BTN_ADMIN_AS_USER, BTN_ADMIN_TOOLS})

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


def admin_mode_button_text(*, admin_tools: bool) -> str:
    return BTN_ADMIN_AS_USER if admin_tools else BTN_ADMIN_TOOLS


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


def menu_keyboard_for_user(telegram_id: int) -> ReplyKeyboardMarkup:
    from bot.services.admin_access import is_admin_listed, is_bot_admin

    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=BTN_CREATE), KeyboardButton(text=BTN_LIST)],
        [KeyboardButton(text=BTN_DIARY), KeyboardButton(text=BTN_STATS)],
    ]
    if is_admin_listed(telegram_id):
        rows.append(
            [KeyboardButton(text=admin_mode_button_text(admin_tools=is_bot_admin(telegram_id)))]
        )
    rows.append([KeyboardButton(text=BTN_MORE)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Например: через 3-4 часа созвон…",
        is_persistent=True,
    )


def menu_keyboard_for_chat(
    chat_id: int,
    telegram_id: int | None = None,
) -> ReplyKeyboardMarkup | None:
    """В группах reply-клавиатура не нужна (и не видна без @бот)."""
    from bot.services.timezone_ctx import is_group_chat

    if is_group_chat(chat_id):
        return None
    if telegram_id is not None:
        return menu_keyboard_for_user(telegram_id)
    return main_menu_keyboard()
