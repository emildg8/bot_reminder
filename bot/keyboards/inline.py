from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.user_prefs import format_snooze_minutes
from bot.texts.messages import DEVELOPER_GITHUB_REPO, DEVELOPER_TELEGRAM, EXAMPLE_PHRASES, TASK_TIME_PRESETS

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
    rows.append([InlineKeyboardButton(text="Другой пояс (UTC)…", callback_data="tz_menu:offset")])
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
                InlineKeyboardButton(text="⏰ Отложить", callback_data=f"szm:{reminder_id}"),
                InlineKeyboardButton(text="✅ Готово", callback_data=f"done:{reminder_id}"),
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit:{reminder_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del_confirm:{reminder_id}"),
            ],
        ]
    )


def snooze_picker_keyboard(
    reminder_id: int,
    minutes: int,
    presets: list[int],
) -> InlineKeyboardMarkup:
    quick_row: list[InlineKeyboardButton] = []
    for preset in presets[:4]:
        label = format_snooze_minutes(preset)
        quick_row.append(
            InlineKeyboardButton(text=label, callback_data=f"szs:{reminder_id}:{preset}")
        )
    rows: list[list[InlineKeyboardButton]] = [quick_row] if quick_row else []
    if len(presets) > 4:
        rows.append([
            InlineKeyboardButton(text=format_snooze_minutes(p), callback_data=f"szs:{reminder_id}:{p}")
            for p in presets[4:6]
        ])
    rows.append([
        InlineKeyboardButton(text="−", callback_data=f"sz-:{reminder_id}"),
        InlineKeyboardButton(text=format_snooze_minutes(minutes), callback_data="sznoop"),
        InlineKeyboardButton(text="+", callback_data=f"sz+:{reminder_id}"),
    ])
    rows.append([
        InlineKeyboardButton(text="✅ Применить", callback_data=f"sza:{reminder_id}"),
        InlineKeyboardButton(text="⬅ Назад", callback_data=f"szb:{reminder_id}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def more_menu_keyboard(telegram_id: int | None = None) -> InlineKeyboardMarkup:
    from bot.services.admin_access import is_admin_listed, is_bot_admin
    from bot.services.admin_mode import more_menu_admin_row

    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="menu:search"),
            InlineKeyboardButton(text="💡 Примеры", callback_data="menu:examples"),
        ],
        [
            InlineKeyboardButton(text="🕐 Часовой пояс", callback_data="menu:timezone"),
            InlineKeyboardButton(text="⚙️ Отложить", callback_data="menu:settings"),
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="menu:about"),
        ],
        [
            InlineKeyboardButton(text="🎯 Тур по боту", callback_data="onb:restart"),
        ],
    ]
    from bot.services.stars_tips import tips_enabled

    if tips_enabled():
        rows.insert(
            -1 if rows else 0,
            [
                InlineKeyboardButton(
                    text="⭐ Поддержать автора",
                    callback_data="menu:thanks",
                )
            ],
        )
    if telegram_id is not None and is_admin_listed(telegram_id):
        admin_row: list[InlineKeyboardButton] = []
        if is_bot_admin(telegram_id):
            admin_row.append(
                InlineKeyboardButton(text="🎛 Админ", callback_data="admin:panel")
            )
        admin_row.extend(more_menu_admin_row(admin_tools=is_bot_admin(telegram_id)))
        rows.append(admin_row)
    rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data="menu:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def list_tabs_keyboard(active: bool, page: int = 0) -> InlineKeyboardMarkup:
    active_label = "📋 Активные ✓" if active else "📋 Активные"
    history_label = "📜 История ✓" if not active else "📜 История"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=active_label, callback_data=f"list:tab:active:{page}"),
                InlineKeyboardButton(text=history_label, callback_data=f"list:tab:history:{page}"),
            ]
        ]
    )


def settings_snooze_keyboard(_presets: list[int], step: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Шаг ±: {step} мин", callback_data="set:step")],
            [
                InlineKeyboardButton(text="Короткие: 5·15·30·60", callback_data="set:pre:std"),
                InlineKeyboardButton(text="Длинные: +1ч·3ч·4ч", callback_data="set:pre:long"),
            ],
            [InlineKeyboardButton(text="⬅ Назад", callback_data="menu:home")],
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


def examples_keyboard(*, back_callback: str | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, (label, _) in enumerate(EXAMPLE_PHRASES):
        row.append(InlineKeyboardButton(text=label, callback_data=f"ex:{idx}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if back_callback:
        rows.append([InlineKeyboardButton(text="◀️ Меню", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ambiguous_hour_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="☀️ 14:00 (дня)", callback_data="ah:day"),
                InlineKeyboardButton(text="🌙 02:00 (ночи)", callback_data="ah:night"),
            ],
        ]
    )


def ambiguous_day_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 09:00", callback_data="ah:morn"),
                InlineKeyboardButton(text="☀️ 14:00", callback_data="ah:day"),
            ],
            [InlineKeyboardButton(text="🌆 18:00", callback_data="ah:night")],
        ]
    )


def assignee_choice_keyboard(candidates: list[str]) -> InlineKeyboardMarkup:
    """as:0 … as:N — индекс в candidates; as:_none — без assignee."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, username in enumerate(candidates[:6]):
        row.append(
            InlineKeyboardButton(text=f"@{username}", callback_data=f"as:{idx}")
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(text="Только мне", callback_data="as:_none"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="as:_cancel"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def about_developer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Telegram",
                    url=f"https://t.me/{DEVELOPER_TELEGRAM}",
                ),
                InlineKeyboardButton(
                    text="⭐ GitHub",
                    url=f"https://github.com/{DEVELOPER_GITHUB_REPO}",
                ),
            ],
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
                InlineKeyboardButton(text="📔 Дневник", callback_data="menu:diary"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"),
            ],
            [
                InlineKeyboardButton(text="⋯ Ещё", callback_data="menu:more"),
            ],
        ]
    )
