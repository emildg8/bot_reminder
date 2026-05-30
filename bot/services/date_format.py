"""Форматирование названий месяцев и дат."""

MONTHS_RU = (
    "",
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)


def format_month_year(dt, *, capitalize: bool = True) -> str:
    label = f"{MONTHS_RU[dt.month]} {dt.year}"
    if capitalize:
        return label[0].upper() + label[1:]
    return label
