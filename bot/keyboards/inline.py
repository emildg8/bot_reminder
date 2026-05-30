from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts.messages import EXAMPLE_PHRASES, TASK_TIME_PRESETS

TIMEZONE_OPTIONS = [
    ("Europe/Moscow", "Москва"),
    ("Europe/Kaliningrad", "Калининград"),
    ("Asia/Yekaterinburg", "Екатеринбург"),
    ("Asia/Novosibirsk", "Новосибирск"),
    ("Asia/Vladivostok", "Владивосток"),
]


def timezone_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"tz:{value}")]
        for value, label in TIMEZONE_OPTIONS
    ]
    rows.append([InlineKeyboardButton(text="UTC offset…", callback_data="tz_menu:offset")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def timezone_offset_keyboard() -> InlineKeyboardMarkup:
    # UTC offsets from -12..+14
    offsets = list(range(-12, 15))
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for off in offsets:
        sign = "+" if off >= 0 else ""
        label = f"UTC{sign}{off}"
        row.append(InlineKeyboardButton(text=label, callback_data=f"tz_off:{off}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="tz_menu:zones")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_reminder_keyboard(draft_id: str, edit_id: int | None = None) -> InlineKeyboardMarkup:
    confirm_data = f"confirm_edit:{edit_id}:{draft_id}" if edit_id else f"confirm:{draft_id}"
    confirm_label = "✅ Сохранить" if edit_id else "✅ Создать"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm_label, callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{draft_id}"),
            ]
        ]
    )


def reminder_actions_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏰ +5", callback_data=f"snooze:{reminder_id}:5"),
                InlineKeyboardButton(text="⏰ +15", callback_data=f"snooze:{reminder_id}:15"),
                InlineKeyboardButton(text="⏰ +30", callback_data=f"snooze:{reminder_id}:30"),
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{reminder_id}"),
                InlineKeyboardButton(text="✅ Готово", callback_data=f"done:{reminder_id}"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{reminder_id}"),
            ],
        ]
    )


def list_page_keyboard(
    page_reminders,
    viewer_telegram_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    for reminder in page_reminders:
        if reminder.created_by_telegram_id != viewer_telegram_id:
            continue
        rows.append(
            [
                InlineKeyboardButton(text=f"#{reminder.id} ✏️", callback_data=f"edit:{reminder.id}"),
                InlineKeyboardButton(text=f"#{reminder.id} 🗑", callback_data=f"del_confirm:{reminder.id}"),
            ]
        )

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"list:page:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="list:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"list:page:{page + 1}"))
    if nav:
        rows.append(nav)

    if not rows:
        return None
    return InlineKeyboardMarkup(inline_keyboard=rows)


def list_manage_keyboard(reminders, viewer_telegram_id: int) -> InlineKeyboardMarkup | None:
    """Legacy wrapper — первая страница."""
    return list_page_keyboard(reminders[:8], viewer_telegram_id, 0, max(1, (len(reminders) + 7) // 8))


def search_page_keyboard(
    page_reminders,
    viewer_telegram_id: int,
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    for reminder in page_reminders:
        if reminder.created_by_telegram_id != viewer_telegram_id:
            continue
        rows.append(
            [
                InlineKeyboardButton(text=f"#{reminder.id} ✏️", callback_data=f"edit:{reminder.id}"),
                InlineKeyboardButton(text=f"#{reminder.id} 🗑", callback_data=f"del_confirm:{reminder.id}"),
            ]
        )

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"search:page:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="search:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"search:page:{page + 1}"))
    if nav:
        rows.append(nav)

    if not rows:
        return None
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirm_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"delete:{reminder_id}"),
                InlineKeyboardButton(text="Отмена", callback_data=f"del_cancel:{reminder_id}"),
            ]
        ]
    )


def task_time_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for label, code in TASK_TIME_PRESETS:
        row.append(InlineKeyboardButton(text=label, callback_data=f"qt:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duplicate_confirm_keyboard(draft_id: str, duplicate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Всё равно создать",
                    callback_data=f"confirm_force:{draft_id}",
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{draft_id}"),
            ],
            [
                InlineKeyboardButton(
                    text=f"✏️ Редактировать #{duplicate_id}",
                    callback_data=f"edit:{duplicate_id}",
                ),
            ],
        ]
    )


def clear_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Да, удалить все", callback_data="clear:yes"),
                InlineKeyboardButton(text="Отмена", callback_data="clear:no"),
            ]
        ]
    )


def examples_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, (label, _) in enumerate(EXAMPLE_PHRASES):
        row.append(InlineKeyboardButton(text=label, callback_data=f"ex:{idx}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Создать", callback_data="menu:create"),
                InlineKeyboardButton(text="📋 Список", callback_data="menu:list"),
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск", callback_data="menu:search"),
                InlineKeyboardButton(text="📊 Статус", callback_data="menu:status"),
            ],
            [
                InlineKeyboardButton(text="💡 Примеры", callback_data="menu:examples"),
                InlineKeyboardButton(text="🕐 Часовой пояс", callback_data="menu:timezone"),
            ],
            [
                InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
            ],
        ]
    )
