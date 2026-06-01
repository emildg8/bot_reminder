"""Group Privacy (BotFather) — влияет на доставку @-сообщений в группах."""

from __future__ import annotations


def format_group_privacy_admin_warning(*, can_read_all_group_messages: bool | None) -> str | None:
    """None — privacy выключен или поле недоступно; иначе текст для админа."""
    if can_read_all_group_messages is not False:
        return None
    return (
        "⚠️ <b>Group Privacy включён</b>\n\n"
        "Бот не получает @, набранный вручную — пользователи видят тишину.\n"
        "Работает: <code>/remind@бот …</code> или @ из списка.\n\n"
        "BotFather → Bot Settings → Group Privacy → <b>Turn off</b>."
    )


def format_group_privacy_status(*, can_read_all_group_messages: bool | None) -> str:
    if can_read_all_group_messages is True:
        return "Group Privacy: <b>выкл</b> (ручной @ доходит)"
    if can_read_all_group_messages is False:
        return "Group Privacy: <b>вкл</b> — /remind или @ из списка"
    return "Group Privacy: <b>?</b>"


def format_group_privacy_user_hint(*, can_read_all_group_messages: bool | None) -> str:
    """Блок для welcome в группе, если privacy включён."""
    if can_read_all_group_messages is not False:
        return ""
    return (
        "\n\n🔒 <b>Group Privacy включён</b> (BotFather)\n"
        "Ручной @ бот <b>не получает</b> — ответа не будет.\n"
        "✅ Работает: <code>/remind@бот …</code> или @ из списка.\n"
        "Админам: BotFather → Group Privacy → <b>Turn off</b>."
    )


def format_group_at_manual_warning() -> str:
    return "⚠️ @, набранный вручную, бот может не увидеть — используй /remind@бот или @ из списка."
