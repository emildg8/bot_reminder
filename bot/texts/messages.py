"""Тексты интерфейса — единый тон и оформление."""

import re
from html import escape

from bot.services.chat_ctx import ChatKind, collective_noun
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

def format_group_welcome(bot_username: str | None = None, *, privacy_hint: str = "") -> str:
    at = f"@{bot_username}" if bot_username else "@бот"
    uname = bot_username or "бот"
    return (
        f"👋 <b>{BOT_NAME}</b> теперь в этой группе!\n\n"
        f"✅ <b>Надёжно</b> — <code>/remind@{uname} через 30 минут созвон</code>\n"
        f"• <code>/remind@{uname} @user завтра в 14:00 задача</code>\n"
        f"• ответ на сообщение + <code>/remind@{uname} …</code>\n\n"
        f"Или {at} <b>из списка</b> + @user + фраза.\n\n"
        "⚠️ @ с клавиатуры бот может не увидеть — выбирай из списка Telegram."
        f"{privacy_hint}\n\n"
        "📋 /list · ❓ /help · 🕐 /timezone · 📊 /status"
    )


def format_channel_welcome(bot_username: str | None = None) -> str:
    uname = bot_username or "бот"
    return (
        f"👋 <b>{BOT_NAME}</b> в канале.\n\n"
        "Напоминания публикуются <b>в канал</b>, кнопки «Отложить / Готово» — "
        "в личке у создавшего админа.\n\n"
        f"✅ Создать: <code>/remind@{uname} завтра в 10:00 пост</code>\n"
        f"• <code>/remind@{uname} через 2 часа проверить</code>\n\n"
        "📋 /list · 🕐 /timezone · /help\n"
        "⏸ /pause · /resume — только админы канала."
    )


def format_collective_welcome(
    chat_kind: ChatKind,
    bot_username: str | None = None,
    *,
    privacy_hint: str = "",
) -> str:
    if chat_kind == ChatKind.CHANNEL:
        return format_channel_welcome(bot_username)
    return format_group_welcome(bot_username, privacy_hint=privacy_hint)


GROUP_WELCOME = format_group_welcome()

GROUP_EXAMPLES_INTRO = "💡 <b>Примеры</b> — нажми, бот попросит подтвердить в личке:"


def format_group_commands_hint(bot_username: str | None = None) -> str:
    uname = bot_username or "бот"
    at = f"@{uname}"
    return (
        f"📋 <b>Команды в группе</b>\n\n"
        f"• <code>/remind@{uname} через 30 минут …</code>\n"
        f"• <code>/remind@{uname} @user …</code> — напоминание участнику\n"
        f"• ответ на сообщение + <code>/remind@{uname} …</code>\n"
        f"• {at} <b>из списка</b> + @user + фраза\n\n"
        "📋 /list · ❓ /help · 🕐 /timezone · 📊 /status"
    )


def format_group_menu_home(bot_username: str | None = None) -> str:
    uname = bot_username or "бот"
    at = f"@{uname}"
    return (
        f"📋 <b>Меню группы</b>\n\n"
        f"✅ <code>/remind@{uname} через час …</code>\n"
        f"Или {at} + @user + фраза · ответ + /remind\n"
        "📔 Дневник — только в личке."
    )


def format_group_create_hint(bot_username: str | None = None) -> str:
    uname = bot_username or "бот"
    at = f"@{uname}"
    return (
        "✍️ <b>Как создать</b>\n\n"
        f"• <code>/remind@{uname} через час созвон</code> — всегда работает\n"
        f"• <code>/remind@{uname} @user завтра в 14:00 задача</code> — на участника\n"
        f"• ответ на сообщение + <code>/remind@{uname} завтра задача</code>\n"
        f"• {at} <b>из списка</b> + @user + фраза\n\n"
        "⚠️ @ вручную — бот может не увидеть; выбирай @ из списка Telegram.\n"
        "Подтверждение и кнопки — в личке с ботом."
    )


def format_group_private_only() -> str:
    return "📔 Дневник и статистика — открой бота в личке и нажми /start."


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
    "• «каждый день в девять зарядка»\n"
    "• «по будням в девять стендап»\n\n"
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


def format_ambiguous_hour_prompt(task: str, day: str, hour: int) -> str:
    day_label = day.capitalize()
    return (
        f"🕐 <b>Уточни время</b>\n\n"
        f"«{day_label} в {hour}» — это день или ночь?\n\n"
        f"Задача: <b>{task}</b>"
    )


def format_ambiguous_day_prompt(task: str, day: str) -> str:
    day_label = day.capitalize()
    return (
        f"🕐 <b>Уточни время</b>\n\n"
        f"«{day_label} …» — во сколько напомнить?\n\n"
        f"Задача: <b>{task}</b>"
    )


def format_pending_ambiguous_hint() -> str:
    return "🕐 Сначала выбери время кнопкой ↑ или отмени: /cancel"


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


def format_parse_fail(
    phrase: str,
    *,
    source: str = "",
    heard: str = "",
    chat_kind: ChatKind = ChatKind.PRIVATE,
    bot_username: str | None = None,
) -> str:
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
        body = f"🎤 Распознано: {heard.strip()}\n\n{body}"
    if chat_kind in (ChatKind.GROUP, ChatKind.SUPERGROUP):
        uname = bot_username or "бот"
        body += f"\n\n💡 В группе: <code>/remind@{uname} через час …</code>"
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

EDIT_HINT = (
    "\n\n💡 Изменить: кнопка <b>✏️</b> в /list или <code>/edit N новая фраза</code>"
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
        + _about_tips_line()
        + "Команды: /help · /list · /journal · /stats"
    )


def _about_tips_line() -> str:
    from bot.services.stars_tips import tips_enabled

    if tips_enabled():
        return "Нравится бот? Добровольная благодарность: /thanks\n\n"
    return ""

GROUP_CREATED_SUFFIX = ""
CHANNEL_CREATED_SUFFIX = ""


def collective_created_suffix(chat_kind: ChatKind) -> str:
    return ""


def format_collective_confirm_prefix(chat_kind: ChatKind) -> str:
    return ""


def format_collective_dm_confirm_header(chat_kind: ChatKind, chat_title: str | None) -> str:
    title = chat_title or collective_noun(chat_kind)
    return f"📣 <b>{title}</b>\n\n"


def format_collective_check_dm(chat_kind: ChatKind, chat_title: str | None) -> str:
    return "👌 Подтвердите в личке с ботом"


def format_collective_dm_failed_fallback(bot_username: str | None) -> str:
    uname = bot_username or "бот"
    return (
        f"⚠️ Не могу написать в личку.\n"
        f"1) <a href=\"https://t.me/{uname}?start=group\">Открыть @{uname}</a> и нажми Start\n"
        f"2) Или подтверди кнопкой здесь"
    )


def format_collective_created_notice(
    *,
    creator_username: str | None,
    creator_user_id: int,
    reminder_id: int,
    when: str,
    text: str,
    chat_kind: ChatKind,
    mention_user_id: int | None = None,
    mention_username: str | None = None,
    mention_source: str | None = None,
) -> str:
    if creator_username:
        who = f"@{creator_username}"
    else:
        who = f'<a href="tg://user?id={creator_user_id}">участник</a>'
    assignee = format_assignee_compact(
        mention_user_id, mention_username, source=mention_source
    )
    suffix = f" · {assignee}" if assignee else ""
    return f"✅ {who} · #{reminder_id} · {when} · <b>{text}</b>{suffix}"


def format_collective_batch_notice(
    *,
    creator_username: str | None,
    creator_user_id: int,
    count: int,
    chat_kind: ChatKind,
) -> str:
    if creator_username:
        who = f"@{creator_username}"
    else:
        who = f'<a href="tg://user?id={creator_user_id}">участник</a>'
    return f"✅ {who} · {count} напоминаний · /list"


def format_group_tz_onboarding() -> str:
    return (
        "🕐 <b>Часовой пояс группы</b>\n\n"
        "От него зависят «завтра в 10:00» и другие напоминания.\n"
        "Выбери город (только админы):"
    )



HELP_TEXT_PRIVATE = f"""\
<b>{BOT_NAME}</b> · v{__version__}

Создавай напоминания <b>текстом</b>, <b>голосом</b> или <b>кружочком</b>.

<b>Голосом</b> — одной фразой: когда + что
• «завтра в два часа дня созвон»
• «через час выпить таблетки»

<b>Примеры</b>
• через 30 минут выпить таблетки
• завтра в 14:00 созвон
• каждый день в 9:00 зарядка
• по будням в 09:00 стендап

<b>Изменить / удалить</b>
• кнопки ✏️ 🗑 в /list
• <code>/edit N завтра в 10:00 новый текст</code>
• <code>/delete N</code>

<b>Команды</b>
/start · /list · /history · /journal · /stats · /about
/search · /edit · /settings · /timezone · /export · /help"""

HELP_TEXT_GROUP = f"""\
<b>{BOT_NAME}</b> в группе · v{__version__}

<b>Создать</b> — надёжно:
<code>/remind@бот через 1 час созвон</code>
<code>/remind@бот @user завтра в 14:00 задача</code>

👤 <b>На участника</b> — три способа:
1. <code>/remind@бот @ivan через 1 час созвон</code> (@ivan из списка)
2. @бот из списка + @user + фраза
3. <b>Ответ</b> на сообщение человека + <code>/remind@бот завтра задача</code>

⚠️ @ с клавиатуры бот может не увидеть — выбирай из списка Telegram.

💬 <b>Группа обсуждений канала</b> — /remind публикует в канал, confirm в личке.

<b>Управление своими</b>
• <code>/edit 24</code> — изменить
• <code>/delete 24</code> или <code>/delete 24 yes</code> — удалить своё

<b>Команды</b>
/list · /edit · /delete · /pause · /resume · /timezone · /status · /help

Срабатывание — в группу. Кнопки ✏️🗑 — в личке."""

HELP_TEXT_CHANNEL = f"""\
<b>{BOT_NAME}</b> в канале · v{__version__}

<b>Создать</b> (админ канала):
<code>/remind@бот завтра в 10:00 пост</code>
<code>/remind@бот через 2 часа проверить</code>

💬 То же работает из <b>группы обсуждений</b> — пост появится в канале.

<b>Команды</b>
/list · /pause · /resume · /timezone · /status · /help

Публикация — в канал, кнопки — в личку создателю."""


def format_help(chat_kind: ChatKind = ChatKind.PRIVATE) -> str:
    if chat_kind == ChatKind.CHANNEL:
        return HELP_TEXT_CHANNEL
    if chat_kind in (ChatKind.GROUP, ChatKind.SUPERGROUP):
        return HELP_TEXT_GROUP
    text = HELP_TEXT_PRIVATE
    from bot.services.stars_tips import tips_enabled

    if tips_enabled():
        text += "\n/thanks — благодарность автору Stars (добровольно)"
    return text


HELP_TEXT = HELP_TEXT_PRIVATE

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


def format_delay_label(seconds: int) -> str:
    if seconds < 60:
        return f"через {seconds} сек от подтверждения"
    if seconds % 3600 == 0 and seconds >= 3600:
        h = seconds // 3600
        return f"через {h} ч от подтверждения"
    if seconds % 60 == 0:
        return f"через {seconds // 60} мин от подтверждения"
    return f"через {seconds // 60} мин от подтверждения"


def format_group_reminder_hint(bot_username: str | None = None) -> str:
    link = f"@{bot_username}" if bot_username else "бота"
    return f"📲 Кнопки управления — в личке. Нет сообщений? /start у {link}"


def format_discussion_channel_hint(bot_username: str | None = None) -> str:
    link = f"@{bot_username}" if bot_username else "бота"
    return (
        "💡 Группа обсуждений канала — добавь "
        f"{link} в канал с правом публикации."
    )

def format_collective_dm_fired(reminder_id: int, text: str) -> str:
    return f"⏰ #{reminder_id} · {text}"


def format_dm_failed_in_group(
    creator_user_id: int,
    *,
    creator_username: str | None = None,
    bot_username: str | None = None,
) -> str:
    who = f"@{creator_username}" if creator_username else f'<a href="tg://user?id={creator_user_id}">создатель</a>'
    link = bot_username or "бота"
    return f"👤 {who}, напиши /start @{link} — кнопки управления в личке"


def format_assignee_compact(
    mention_user_id: int | None,
    mention_username: str | None,
    *,
    source: str | None = None,
) -> str:
    """Короткая строка «кому» для success-сообщений."""
    if not mention_user_id and not mention_username:
        return ""
    icon = "↩️" if source == "reply" else "👤"
    if mention_user_id and mention_username:
        who = f'<a href="tg://user?id={mention_user_id}">@{escape(mention_username)}</a>'
    elif mention_user_id:
        who = f'<a href="tg://user?id={mention_user_id}">участник</a>'
    else:
        who = f"@{escape(mention_username or '')}"
    return f"{icon} {who}"


def format_mention_assignee_line(
    mention_user_id: int | None,
    mention_username: str | None,
    *,
    resolved: bool = True,
    source: str | None = None,
) -> str:
    """Строка «кому» для confirm-карточки."""
    if not mention_user_id and not mention_username:
        return ""

    if mention_username and not resolved:
        return (
            f"⚠️ @{escape(mention_username)} не в этом чате или не найден — "
            "напомню создателю.\n\n"
        )

    if mention_user_id and mention_username:
        who = f'<a href="tg://user?id={mention_user_id}">@{escape(mention_username)}</a>'
    elif mention_user_id:
        who = f'<a href="tg://user?id={mention_user_id}">участник</a>'
    elif mention_username:
        who = f"@{escape(mention_username)}"
    else:
        return ""

    if source == "reply":
        return f"↩️ <b>Кому:</b> {who} <i>(ответ на сообщение)</i>\n\n"
    return f"👤 <b>Кому:</b> {who}\n\n"


def format_confirm_card(summary: str, *, is_edit: bool = False) -> str:
    header = CONFIRM_EDIT_HEADER if is_edit else CONFIRM_CREATE_HEADER
    return f"{header}\n\n{summary}\n\nПодтверди действие:"


def format_created(
    reminder_id: int,
    when: str,
    text: str,
    *,
    in_group: bool = False,
    collective: ChatKind | None = None,
    mention_user_id: int | None = None,
    mention_username: str | None = None,
    mention_source: str | None = None,
) -> str:
    body = (
        f"✅ <b>Готово!</b> Напоминание #{reminder_id}\n\n"
        f"🕐 {when}\n"
        f"📝 {text}"
    )
    assignee = format_assignee_compact(
        mention_user_id, mention_username, source=mention_source
    )
    if assignee:
        body += f"\n{assignee}"
    kind = collective
    if kind is None and in_group:
        kind = ChatKind.SUPERGROUP
    if kind is not None and kind != ChatKind.PRIVATE:
        body += collective_created_suffix(kind)
    elif not in_group and collective is None:
        body += EDIT_HINT
    return body


def format_batch_created(
    items: list[tuple[int, str, str]],
    *,
    in_group: bool = False,
    collective: ChatKind | None = None,
) -> str:
    lines = [f"✅ <b>Готово!</b> Создано {len(items)} напоминания:\n"]
    for reminder_id, when, text in items:
        lines.append(f"• #{reminder_id} · {when} · {text}")
    kind = collective
    if kind is None and in_group:
        kind = ChatKind.SUPERGROUP
    if kind is not None and kind != ChatKind.PRIVATE:
        lines.append(collective_created_suffix(kind))
    return "\n".join(lines)


def format_updated(reminder_id: int, when: str) -> str:
    return f"✏️ Напоминание #{reminder_id} обновлено.\n🕐 Следующий раз: <b>{when}</b>"


def format_edit_replaced(
    old_id: int,
    items: list[tuple[int, str, str]],
    *,
    in_group: bool = False,
    collective: ChatKind | None = None,
) -> str:
    lines = [f"✅ Напоминание #{old_id} заменено на <b>{len(items)}</b>:\n"]
    for reminder_id, when, text in items:
        lines.append(f"• #{reminder_id} · {when} · {text}")
    kind = collective
    if kind is None and in_group:
        kind = ChatKind.SUPERGROUP
    if kind is not None and kind != ChatKind.PRIVATE:
        lines.append(collective_created_suffix(kind))
    return "\n".join(lines)


def format_status(
    *,
    count: int,
    paused: bool,
    tz: str,
    tz_scope: str,
    version: str = __version__,
    chat_kind: ChatKind = ChatKind.PRIVATE,
    next_line: str | None = None,
    delivery_line: str | None = None,
    post_ok: bool | None = None,
    admin_mode_line: str | None = None,
    tips_line: str | None = None,
) -> str:
    tz_label = format_timezone_label(tz)
    state = "⏸ на паузе" if paused else "▶️ активны"
    extra = ""
    if chat_kind == ChatKind.PRIVATE:
        extra = "\n\n📔 Дневник: /journal · 📜 История: /history"
    lines = [
        f"📊 <b>Статус</b> · v{version}\n",
        f"📋 Активных: <b>{count}</b>",
        f"⚡️ Состояние: {state}",
        f"🕐 Часовой пояс ({tz_scope}): <b>{tz_label}</b>",
    ]
    if delivery_line:
        lines.append(delivery_line)
    if next_line:
        lines.append(next_line)
    if post_ok is False:
        lines.append("⚠️ Бот <b>не может писать</b> в чат доставки — дай права или сделай админом")
    elif post_ok is True and chat_kind != ChatKind.PRIVATE:
        lines.append("✅ Бот может публиковать напоминания")
    if admin_mode_line:
        lines.append(admin_mode_line)
    if tips_line:
        lines.append(tips_line)
    return "\n".join(lines) + extra


def format_admin_mode_ack(*, admin_tools: bool) -> str:
    if admin_tools:
        return "✅ <b>Режим администратора</b> — инструменты ops включены."
    return "✅ <b>Режим пользователя</b> — тестируешь бота как обычный аккаунт."


def format_admin_mode_status(*, admin_tools: bool) -> str:
    if admin_tools:
        return (
            "🛠 <b>Режим администратора</b>\n\n"
            "<b>Сейчас доступно</b>\n"
            "• <code>/admin</code> — панель · кнопка 🎛 ниже\n"
            "• /health · /sysinfo · /userinfo · /admins\n"
            "• /update · /broadcast\n"
            "• В группах — /pause и /clear без админа чата\n\n"
            "Проверить UX пользователя: кнопка «👤 Как пользователь» внизу "
            "или <code>/adminmode user</code>"
        )
    return (
        "👤 <b>Режим пользователя</b>\n\n"
        "<b>Сейчас как у обычного аккаунта</b>\n"
        "• Админ-команды скрыты (попробуй /health — подсказка)\n"
        "• В группах — только свои напоминания\n\n"
        "<code>/adminmode</code> и кнопка «🛠 Режим админа» всегда под рукой.\n"
        "Ops-уведомления о падении бота приходят в любом режиме."
    )


def format_admin_mode_line(*, admin_tools: bool) -> str:
    if admin_tools:
        return "🛠 Режим: <b>администратор</b> · /adminmode"
    return "👤 Режим: <b>пользователь</b> · /adminmode"


def format_admin_help_footer(*, admin_tools: bool) -> str:
    if admin_tools:
        return (
            "🛠 <b>Админ бота</b> — режим <b>администратора</b>\n"
            "/adminmode — переключить на пользовательский для теста UX"
        )
    return (
        "👤 <b>Админ бота</b> — режим <b>пользователя</b> (тест UX)\n"
        "/adminmode admin — вернуть /health, /sysinfo и др."
    )


def format_ping_admin_suffix(*, admin_tools: bool) -> str:
    if admin_tools:
        return " · 🛠 admin"
    return " · 👤 user-test"
