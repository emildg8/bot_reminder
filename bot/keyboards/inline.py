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
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_reminder_keyboard(draft_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать", callback_data=f"confirm:{draft_id}"),
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
                InlineKeyboardButton(text="✅ Готово", callback_data=f"done:{reminder_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{reminder_id}"),
            ],
        ]
    )


def list_reminder_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{reminder_id}")]
        ]
    )
