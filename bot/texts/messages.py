"""Тексты интерфейса — единый тон и оформление."""

import re

from bot.services.timezone_labels import format_timezone_label
from bot.version import __version__

BOT_NAME = "Напоминалка"

_TIME_HINT = re.compile(
    r"через|завтра|сегодня|послезавтра|кажд|будня|выходн|ежедневн|"
    r"\d{1,2}[:.]\d{2}|"
    r"(?<!\w)(?:час|минут|мин)(?!\w)",
    re.IGNORECASE,
)

WELCOME_ONBOARDING = (
    f"👋 <b>Добро пожаловать в {BOT_NAME}!</b>\n\n"
    "Я помогу не забыть важное — текстом, голосом или кружочком.\n\n"
    "🕐 Сначала выбери часовой пояс — от него зависит время напоминаний:"
)

WELCOME_BACK = (
    f"👋 <b>{BOT_NAME}</b>\n\n"
    "Напиши фразу, отправь голос или кружочек — я разберу время и создам напоминание.\n\n"
    "🕐 Часовой пояс ({tz_scope}): <b>{tz_label}</b>"
)

GROUP_WELCOME = (
    f"👋 <b>{BOT_NAME}</b> теперь в этой группе!\n\n"
    "Напиши, например:\n"
    "• <code>через 30 минут созвон</code>\n"
    "• <code>по будням в 09:00 стендап</code>\n"
    "• <code>@username через 1 час задача</code>\n\n"
    "🕐 Часовой пояс группы: /timezone\n"
    "📋 Список: /list · 🔍 Поиск: /search"
)

CREATE_HINT = (
    "✍️ <b>Создать напоминание</b>\n\n"
    "Одной фразой — текстом, голосом или кружочком:\n"
    "<code>через 30 минут выпить таблетки</code>"
)

PARSE_FAIL = (
    "🤔 <b>Не понял время</b>\n\n"
    "Попробуй так:\n"
    "• <code>через 30 минут выпить таблетки</code>\n"
    "• <code>через час созвон</code>\n"
    "• <code>завтра в 14:00 созвон</code>\n"
    "• <code>каждый день в 9:00 зарядка</code>\n"
    "• <code>каждые 2 часа встать</code>\n"
    "• <code>по будням в 09:00 стендап</code>\n\n"
    "💡 Нажми «Примеры» или /help"
)

PARSE_FAIL_TASK_ONLY = (
    "🤔 <b>Не вижу время</b>\n\n"
    "Задача: <b>{task}</b>\n\n"
    "Выбери когда напомнить 👇"
)

TASK_TIME_PRESETS: list[tuple[str, str]] = [
    ("⏱ +30 мин", "30m"),
    ("⏱ +1 час", "1h"),
    ("📅 Завтра 9:00", "tom9"),
    ("📅 Завтра 14:00", "tom14"),
]


def phrase_from_task_preset(task: str, code: str) -> str:
    templates = {
        "30m": "через 30 минут {task}",
        "1h": "через час {task}",
        "tom9": "завтра в 9:00 {task}",
        "tom14": "завтра в 14:00 {task}",
    }
    template = templates.get(code, "через час {task}")
    return template.format(task=task.strip())


def looks_like_task_only(text: str) -> bool:
    return bool(text.strip()) and not _TIME_HINT.search(text)


def format_parse_fail(phrase: str) -> str:
    task = " ".join(phrase.strip().split()[:6]) or "задача"
    if looks_like_task_only(phrase):
        return PARSE_FAIL_TASK_ONLY.format(task=task)
    return PARSE_FAIL

CONFIRM_CREATE_HEADER = "📌 <b>Проверь напоминание</b>"
CONFIRM_EDIT_HEADER = "✏️ <b>Изменить напоминание</b>"

HELP_TEXT = f"""\
<b>{BOT_NAME}</b> · v{__version__}

Создавай напоминания <b>текстом</b>, <b>голосом</b> или <b>кружочком</b>.

<b>Примеры фраз</b>
• через 30 минут выпить таблетки
• через час созвон
• завтра в 14:00 созвон
• каждые 2 часа встать
• каждый день в 9:00 зарядка
• по будням в 09:00 стендап
• пн ср пт в 10:00 тренировка

<b>Команды</b>
/start · /list · /search · /edit
/pause · /resume · /timezone · /status
/export · /import · /clear · /help

<b>Группы</b>
<code>@username через 1 час задача</code> — напомнить участнику.
Кнопки управления приходят создателю в личку с ботом."""

EXAMPLE_PHRASES: list[tuple[str, str]] = [
    ("⏱ Через час", "через час созвон"),
    ("📅 Завтра 14:00", "завтра в 14:00 созвон"),
    ("⏱ Через 30 мин", "через 30 минут выпить таблетки"),
    ("📅 Каждый день 9:00", "каждый день в 9:00 зарядка"),
    ("🔁 Каждые 2 часа", "каждые 2 часа встать"),
    ("💼 По будням", "по будням в 09:00 стендап"),
    ("🏋 Пн ср пт", "пн ср пт в 10:00 тренировка"),
    ("🌴 По выходным", "по выходным в 11:00 уборка"),
    ("📆 Каждый понедельник", "каждый понедельник в 9:00 отчёт"),
]

EXAMPLES_INTRO = "💡 <b>Нажми пример</b> — бот подставит фразу и распознает время:"


def format_confirm_card(summary: str, *, is_edit: bool = False) -> str:
    header = CONFIRM_EDIT_HEADER if is_edit else CONFIRM_CREATE_HEADER
    return f"{header}\n\n{summary}\n\nПодтверди действие:"


def format_created(reminder_id: int, when: str, text: str) -> str:
    return (
        f"✅ <b>Готово!</b> Напоминание #{reminder_id}\n\n"
        f"🕐 {when}\n"
        f"📝 {text}"
    )


def format_updated(reminder_id: int, when: str) -> str:
    return f"✏️ Напоминание #{reminder_id} обновлено.\n🕐 Следующий раз: <b>{when}</b>"


def format_status(
    *,
    count: int,
    paused: bool,
    tz: str,
    tz_scope: str,
    version: str = __version__,
) -> str:
    tz_label = format_timezone_label(tz)
    state = "⏸ на паузе" if paused else "▶️ активны"
    return (
        f"📊 <b>Статус</b> · v{version}\n\n"
        f"📋 Напоминаний: <b>{count}</b>\n"
        f"⚡️ Состояние: {state}\n"
        f"🕐 Часовой пояс ({tz_scope}): <b>{tz_label}</b>"
    )
