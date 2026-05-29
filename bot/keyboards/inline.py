from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
                InlineKeyboardButton(text="+5 мин", callback_data=f"snooze:{reminder_id}:5"),
                InlineKeyboardButton(text="+15 мин", callback_data=f"snooze:{reminder_id}:15"),
                InlineKeyboardButton(text="+30 мин", callback_data=f"snooze:{reminder_id}:30"),
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
                InlineKeyboardButton(text=f"#{reminder.id} 🗑", callback_data=f"delete:{reminder.id}"),
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


def clear_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Да, удалить все", callback_data="clear:yes"),
                InlineKeyboardButton(text="Отмена", callback_data="clear:no"),
            ]
        ]
    )


def main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Создать", callback_data="menu:create"),
                InlineKeyboardButton(text="📋 Список", callback_data="menu:list"),
            ],
            [
                InlineKeyboardButton(text="🕐 Часовой пояс", callback_data="menu:timezone"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
            ],
            [InlineKeyboardButton(text="💡 Примеры", callback_data="menu:examples")],
        ]
    )
