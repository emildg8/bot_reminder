"""Поиск напоминаний — общая логика для /search и кнопки меню."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aiogram.types import CallbackQuery, Message

from bot.db.repository import async_session, get_reminder, search_chat_reminders
from bot.keyboards.inline import search_page_keyboard
from bot.keyboards.reply import menu_keyboard_for_chat
from bot.services.reminder_display import format_reminder_list_line
from bot.services.reminders_ui import _paginate

SEARCH_CACHE_TTL = timedelta(minutes=10)


@dataclass
class SearchCache:
    query: str
    chat_id: int
    reminder_ids: list[int]
    created_at: datetime


_search_cache: dict[int, SearchCache] = {}


def _store_cache(user_id: int, chat_id: int, query: str, reminder_ids: list[int]) -> None:
    _search_cache[user_id] = SearchCache(
        query=query,
        chat_id=chat_id,
        reminder_ids=reminder_ids,
        created_at=datetime.now(timezone.utc),
    )


def _get_cache(user_id: int) -> SearchCache | None:
    entry = _search_cache.get(user_id)
    if entry is None:
        return None
    if datetime.now(timezone.utc) - entry.created_at > SEARCH_CACHE_TTL:
        _search_cache.pop(user_id, None)
        return None
    return entry


async def _fetch_cached_reminders(user_id: int) -> tuple[SearchCache, list] | None:
    cache = _get_cache(user_id)
    if cache is None:
        return None
    async with async_session() as session:
        reminders = []
        for rid in cache.reminder_ids:
            if r := await get_reminder(session, rid):
                if r.is_active:
                    reminders.append(r)
    return cache, reminders


def _format_search_body(query: str, total: int, page: int, total_pages: int, lines: list[str]) -> str:
    header = f"🔍 <b>Найдено: {total}</b> · «{query}»"
    if total_pages > 1:
        header += f" · стр. {page + 1}/{total_pages}"
    return header + "\n\n" + "\n".join(lines)


def prune_expired_search_cache() -> int:
    now = datetime.now(timezone.utc)
    removed = 0
    for uid in list(_search_cache.keys()):
        entry = _search_cache.get(uid)
        if entry and now - entry.created_at > SEARCH_CACHE_TTL:
            _search_cache.pop(uid, None)
            removed += 1
    return removed


async def send_search_results(message: Message, query: str, page: int = 0) -> None:
    async with async_session() as session:
        results = await search_chat_reminders(session, message.chat.id, query)

    if not results:
        await message.answer(
            f"🔍 По запросу «{query}» ничего не найдено.",
            reply_markup=menu_keyboard_for_chat(message.chat.id),
        )
        return

    _store_cache(message.from_user.id, message.chat.id, query, [r.id for r in results])
    page_items, page, total_pages = _paginate(results, page)
    lines = [format_reminder_list_line(r, r.timezone) for r in page_items]
    keyboard = search_page_keyboard(page_items, message.from_user.id, page, total_pages)
    await message.answer(
        _format_search_body(query, len(results), page, total_pages, lines),
        reply_markup=keyboard or menu_keyboard_for_chat(message.chat.id),
    )


async def edit_search_page(callback: CallbackQuery, page: int) -> None:
    cached = await _fetch_cached_reminders(callback.from_user.id)
    if cached is None:
        await callback.answer("Поиск устарел — повтори запрос.", show_alert=True)
        return

    cache, results = cached
    if not results:
        await callback.message.edit_text(f"🔍 По запросу «{cache.query}» ничего не найдено.")
        await callback.answer()
        return

    page_items, page, total_pages = _paginate(results, page)
    lines = [format_reminder_list_line(r, r.timezone) for r in page_items]
    keyboard = search_page_keyboard(page_items, callback.from_user.id, page, total_pages)
    await callback.message.edit_text(
        _format_search_body(cache.query, len(results), page, total_pages, lines),
        reply_markup=keyboard,
    )
    await callback.answer()
