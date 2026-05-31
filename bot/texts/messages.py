"""Тексты интерфейса — единый тон и оформление."""

import re

from bot.services.timezone_labels import format_timezone_label
from bot.version import __version__

BOT_NAME = "Напоминалка"

_TIME_HINT = re.compile(
    r"через\s+(?:\d+|пару|несколько|полчаса|полтора|"
    r"один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|"
    r"одиннадцать|двенадцать|час|мин|\d+\s*[-–—]\s*\d+)|"
    r"(?:завтра|сегодня|послезавтра)\s+(?:в\s+)?(?:\d{1,2}|"
    r"один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|"
    r"одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|"
    r"шестнадцать|семнадцать|восемнадцать|девятнадцать|двадцать)"
    r"(?:\s*(?:час(?:а|ов)?\s+)?(?:дня|утра|вечера|ночи|днем|утром|вечером|ночью)|"
    r"[:.]\d{2})|"
    r"(?:завтра|сегодня|послезавтра)\s+(?:утром|днем|дня|вечером|ночью|утра|вечера|ночи)\b|"
    r"\d{1,2}[:.]\d{2}|"
    r"полдень|полночь|полтора\s+дня|"
    r"к\s+обед|к\s+вечер|к\s+утр|"
    r"кажд|будня|выходн|ежедневн|"
    r"(?<!\w)(?:недел)(?!\w)",
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
    "📋 Список · 📔 Дневник · 📊 Статистика — кнопки внизу.\n"
    "🕐 Часовой пояс ({tz_scope}): <b>{tz_label}</b>"
)

def format_group_welcome(bot_username: str | None = None) -> str:
    at = f"@{bot_username}" if bot_username else "@бот"
    return (
        f"👋 <b>{BOT_NAME}</b> теперь в этой группе!\n\n"
        f"В группе бот видит только сообщения с {at} или команды (/list и т.д.).\n"
        f"Каждую фразу начинай с {at}:\n"
        f"• <code>{at} через 30 минут созвон</code>\n"
        f"• <code>{at} по будням в 09:00 стендап</code>\n"
        f"• <code>@username {at} через 1 час задача</code>\n\n"
        "💡 «Не имеет доступа к сообщениям» в профиле бота — нормально: "
        f"без {at} он не увидит текст.\n\n"
        "🕐 Часовой пояс группы: /timezone\n"
        "📋 Список: /list · 📜 История: /history"
    )


GROUP_WELCOME = format_group_welcome()

CREATE_HINT = (
    "✍️ <b>Создать напоминание</b>\n\n"
    "Одной фразой — текстом, голосом или кружочком:\n"
    "<code>через 3-4 часа созвон</code>\n"
    "<code>завтра в два часа дня созвон</code>\n\n"
    "🎤 Голосом: скажи <b>когда</b> и <b>что</b> одной фразой"
)

PARSE_FAIL = (
    "🤔 <b>Не понял время</b>\n\n"
    "Попробуй так:\n"
    "• <code>через 3-4 часа созвон</code>\n"
    "• <code>через пару часов обед</code>\n"
    "• <code>завтра в 14:00 созвон</code>\n"
    "• <code>каждый день в 9:00 зарядка</code>\n"
    "• <code>каждые 2 часа встать</code>\n"
    "• <code>по будням в 09:00 стендап</code>\n\n"
    "💡 Нажми «Примеры» или /help"
)

PARSE_FAIL_VOICE = (
    "🤔 <b>Не понял время из голоса</b>\n\n"
    "Скажи одной короткой фразой: <b>когда</b> + <b>что</b>\n"
    "• «завтра в два часа дня созвон»\n"
    "• «через час выпить таблетки»\n"
    "• «завтра утром зарядка»\n\n"
    "🎤 Говори чётко, без длинных пауз в начале."
)

PARSE_FAIL_VOICE_TASK = (
    "🤔 <b>Не вижу время</b>\n\n"
    "Задача: <b>{task}</b>\n\n"
    "🎤 Добавь когда: «завтра в 14:00» или «через час»\n"
    "Или выбери кнопку 👇"
)

PARSE_FAIL_TASK_ONLY = (
    "🤔 <b>Не вижу время</b>\n\n"
    "Задача: <b>{task}</b>\n\n"
    "Выбери когда напомнить 👇"
)

TASK_TIME_PRESETS: list[tuple[str, str]] = [
    ("⏱ +30 мин", "30m"),
    ("⏱ +1 час", "1h"),
    ("⏱ +3 часа", "3h"),
    ("⏱ +4 часа", "4h"),
    ("📅 Завтра 9:00", "tom9"),
    ("📅 Завтра 14:00", "tom14"),
]


def phrase_from_task_preset(task: str, code: str) -> str:
    templates = {
        "30m": "через 30 минут {task}",
        "1h": "через час {task}",
        "3h": "через 3 часа {task}",
        "4h": "через 4 часа {task}",
        "tom9": "завтра в 9:00 {task}",
        "tom14": "завтра в 14:00 {task}",
    }
    template = templates.get(code, "через час {task}")
    return template.format(task=task.strip())


def looks_like_task_only(text: str) -> bool:
    return bool(text.strip()) and not _TIME_HINT.search(text)


def format_parse_fail(phrase: str, *, source: str = "", heard: str = "") -> str:
    task = " ".join(phrase.strip().split()[:6]) or "задача"
    is_voice = source in ("voice", "video_note")
    if looks_like_task_only(phrase):
        body = (
            PARSE_FAIL_VOICE_TASK.format(task=task)
            if is_voice
            else PARSE_FAIL_TASK_ONLY.format(task=task)
        )
    elif is_voice:
        body = PARSE_FAIL_VOICE
    else:
        body = PARSE_FAIL
    if is_voice and heard.strip():
        return f"🎤 Распознано: {heard.strip()}\n\n{body}"
    return body

CONFIRM_CREATE_HEADER = "📌 <b>Проверь напоминание</b>"
CONFIRM_EDIT_HEADER = "✏️ <b>Изменить напоминание</b>"

ONBOARDING_READY = (
    "✨ <b>Готово!</b> Попробуй создать первое напоминание:\n\n"
    "• <code>через час созвон</code>\n"
    "• <code>завтра в 14:00 обед</code>\n"
    "• <code>каждый день в 9:00 зарядка</code>\n\n"
    "🎤 Или скажи голосом: «завтра в два часа дня созвон»\n"
    "Или нажми ➕ <b>Создать</b> в меню внизу."
)


def format_about(version: str = __version__) -> str:
    return (
        f"📦 <b>{BOT_NAME}</b> · v{version}\n\n"
        "Telegram-ежедневник: напоминания текстом, голосом или кружочком.\n\n"
        "<b>Возможности</b>\n"
        "• Разовые, интервальные и ежедневные напоминания\n"
        "• Дневник и история за день\n"
        "• Статистика за месяц\n"
        "• Группы и личные чаты\n"
        "• Отложить с настраиваемыми вариантами\n\n"
        "Команды: /help · /list · /journal · /stats"
    )

HELP_TEXT = f"""\
<b>{BOT_NAME}</b> · v{__version__}

Создавай напоминания <b>текстом</b>, <b>голосом</b> или <b>кружочком</b>.

<b>Голосом</b> — одной фразой: когда + что
• «завтра в два часа дня созвон»
• «через час выпить таблетки»
• «завтра утром зарядка»

<b>Примеры фраз</b>
• через 30 минут выпить таблетки
• через 3-4 часа созвон
• через пару часов обед
• завтра в 14:00 созвон
• каждые 2 часа встать
• каждый день в 9:00 зарядка
• по будням в 09:00 стендап
• пн ср пт в 10:00 тренировка

<b>Команды</b>
/start · /list · /history · /journal · /stats · /about
/search · /edit · /cancel · /settings
/pause · /resume · /timezone · /status
/export · /import · /clear · /help

<b>Списки</b>
📋 Список — активные · 📜 История — за сегодня (не удаляется)
📔 Дневник — хронология дня · 📊 Статистика — за месяц

<b>Отложить</b>
Кнопка «⏰ Отложить» открывает счётчик − / + и быстрые варианты. Настройки: /settings

<b>Группы</b>
В группе каждую фразу начинай с <code>@бот</code> (или команда /list).
• <code>@бот через 1 час созвон</code>
• <code>@username @бот через 1 час задача</code> — напомнить участнику.
Кнопки управления приходят создателю в личку с ботом."""

EXAMPLE_PHRASES: list[tuple[str, str]] = [
    ("🎤 К обеду", "завтра к обеду созвон"),
    ("🎤 2 часа дня", "завтра в два часа дня созвон"),
    ("⏱ 3-4 часа", "через 3-4 часа созвон"),
    ("⏱ Пару часов", "через пару часов обед"),
    ("📅 Завтра 14:00", "завтра в 14:00 созвон"),
    ("⏱ Через 30 мин", "через 30 минут выпить таблетки"),
    ("📅 Каждый день 9:00", "каждый день в 9:00 зарядка"),
    ("🔁 Каждые 2 часа", "каждые 2 часа встать"),
    ("💼 По будням", "по будням в 09:00 стендап"),
    ("🏋 Пн ср пт", "пн ср пт в 10:00 тренировка"),
    ("🌴 По выходным", "по выходным в 11:00 уборка"),
    ("📆 Каждый понедельник", "каждый понедельник в 9:00 отчёт"),
]

EXAMPLES_INTRO = "💡 <b>Нажми пример</b> — бот подставит фразу и определит время:"


def format_confirm_card(summary: str, *, is_edit: bool = False) -> str:
    header = CONFIRM_EDIT_HEADER if is_edit else CONFIRM_CREATE_HEADER
    return f"{header}\n\n{summary}\n\nПодтверди действие:"


def format_created(reminder_id: int, when: str, text: str) -> str:
    return (
        f"✅ <b>Готово!</b> Напоминание #{reminder_id}\n\n"
        f"🕐 {when}\n"
        f"📝 {text}"
    )


def format_batch_created(items: list[tuple[int, str, str]]) -> str:
    lines = [f"✅ <b>Готово!</b> Создано {len(items)} напоминания:\n"]
    for reminder_id, when, text in items:
        lines.append(f"• #{reminder_id} · {when} · {text}")
    return "\n".join(lines)


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
        f"📋 Активных: <b>{count}</b>\n"
        f"⚡️ Состояние: {state}\n"
        f"🕐 Часовой пояс ({tz_scope}): <b>{tz_label}</b>\n\n"
        f"📔 Дневник: /journal · 📜 История: /history"
    )
