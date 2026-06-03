"""Общие фильтры message-handlers.

Порядок роутеров в main.py: tips → … → create.
tips ловит USER_PHRASE_TEXT только с tip_custom_text_filter;
create — все остальные фразы (в т.ч. @бот в группе).
"""

from aiogram import F

from bot.keyboards.reply import MENU_BUTTON_TEXTS

USER_PHRASE_TEXT = F.text & ~F.text.startswith("/") & ~F.text.in_(MENU_BUTTON_TEXTS)
