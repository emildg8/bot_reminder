"""Человекочитаемые названия часовых поясов."""

TZ_LABELS: dict[str, str] = {
    "Europe/Moscow": "Москва (UTC+3)",
    "Europe/Kaliningrad": "Калининград (UTC+2)",
    "Asia/Yekaterinburg": "Екатеринбург (UTC+5)",
    "Asia/Novosibirsk": "Новосибирск (UTC+7)",
    "Asia/Vladivostok": "Владивосток (UTC+10)",
    "Etc/UTC": "UTC",
}


def format_timezone_label(tz: str) -> str:
    if tz in TZ_LABELS:
        return TZ_LABELS[tz]
    if tz.startswith("Etc/GMT"):
        # Etc/GMT-3 = UTC+3 (inverted sign in IANA)
        raw = tz.replace("Etc/GMT", "")
        if raw in ("", "+0", "-0"):
            return "UTC"
        try:
            offset = -int(raw) if raw.lstrip("+-") else 0
            sign = "+" if offset >= 0 else ""
            return f"UTC{sign}{offset}"
        except ValueError:
            pass
    return tz.replace("_", " ")
