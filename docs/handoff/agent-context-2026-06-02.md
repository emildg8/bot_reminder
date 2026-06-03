# Handoff для нового агента · 2026-06-02

Скопируй в первое сообщение новому агенту или укажи: «прочитай `docs/handoff/agent-context-2026-06-02.md`».

## Проект

- **Репо:** `d:\Dev\Telegram\bot_reminder` · GitHub `emildg8/bot_reminder`
- **Бот:** Telegram-напоминалка на русском (`@break_remind_bot`)
- **Стек:** Python 3.11+, aiogram, SQLite/PostgreSQL, pytest, ruff
- **Язык ответов пользователю:** русский
- **Коммиты:** только по явной просьбе пользователя

## Текущее состояние (актуально)

| Параметр | Значение |
|----------|----------|
| Версия | **v3.45.8** (`bot/version.py` = `pyproject.toml`) |
| Тесты | **576** (`pytest --collect-only -q`) |
| CI | green на `main` |
| Latest release | [v3.45.8](https://github.com/emildg8/bot_reminder/releases/tag/v3.45.8) |
| HEAD | `b942b21` — fix ruff F401 (unused import) |
| Working tree | clean, `main` = `origin/main` |

## Завершённая работа: «Автор в продукте»

Линия **закрыта** релизом v3.45.8. Фазы 1–2 + polish.

### v3.45.6 — фаза 1
- `format_developer_made_by_line()` после onboarding
- Кнопка **🆕 Что нового** → GitHub release tag
- Блок «Как связаться» в `/author`
- Тизер в `/about`

### v3.45.7 — polish
- После onboarding — inline **👤 Автор** + **🆕 v…** (`developer_made_by_keyboard`)
- `/author` — компактный «Обратная связь»
- `/help` — футер с «что нового» и `/author`
- После Stars — текст «Вопросы и идеи — /author»

### v3.45.8 — фаза 2 (финал)
- `/status` в личке — `format_developer_status_line()` + `author_line` в `chat_status.py`
- После Stars — кнопки **👤 Автор** / **⭐ Ещё раз** (`tip_thank_you_keyboard`)
- `scripts/smoke_author.py` в `verify_ops`
- Гайд [author-presence.md](../guides/author-presence.md)
- Блок «Разработчик / open source» в [yookassa-submission-pack.md](../guides/yookassa-submission-pack.md)

## Ключевые файлы

```
bot/texts/messages.py       # DEVELOPER_*, format_developer_*
bot/keyboards/inline.py     # developer_links_keyboard, developer_made_by_keyboard
bot/handlers/start.py       # made-by после onboarding
bot/handlers/status.py      # /about, /author
bot/handlers/payments.py    # tip_thank_you_keyboard после оплаты
bot/services/chat_status.py # /status + author_line (только личка)
bot/services/stars_tips.py  # tip_thank_you_keyboard
scripts/smoke_author.py     # офлайн-smoke точек входа автора
scripts/verify_ops.py       # 4 smoke: nlp, group_mentions, stars, author
tests/test_about.py         # format_developer_*, keyboard tests
tests/test_stars_tips.py    # test_status_includes_author_line_for_private
docs/guides/author-presence.md
docs/releases/v3.45.8.md
```

## Проверки перед любой работой

```bash
python scripts/verify_ops.py          # → verify_ops OK · v3.45.8
python scripts/smoke_author.py          # → smoke_author OK
ruff check bot tests
pytest tests/test_about.py -q
```

Полный CI как в release.yml: ruff + verify_ops + pytest --cov-fail-under=65.

## Известные нюансы

- **PowerShell** на Windows — HEREDOC для git commit не работает; использовать `git commit -m "..."`.
- **doc_metrics** — в docs только форма **«N тестов»** (не «N тест»), иначе `verify_ops` падает.
- При смене версии/числа тестов — чеклист в [doc-maintenance.md](../guides/doc-maintenance.md).
- Первый push v3.45.8 упал на ruff F401; исправлен в `b942b21`. Тег `v3.45.8` перенесён на HEAD, Release пересоздан успешно.

## Wispbyte (ручное, не сделано агентом)

После деплоя проверить по [ops-checklist.md](../guides/ops-checklist.md):

- [ ] `/ping` → **v3.45.8**
- [ ] `/status` в личке — строка автора
- [ ] `/thanks` → после оплаты кнопки **👤 Автор** / **⭐ Ещё раз**
- [ ] `python scripts/smoke_author.py` на сервере не нужен — только локально/CI

## Открытые задачи (если пользователь продолжит)

**Нет явного backlog от пользователя.** «Автор в продукте» завершён.

Возможные следующие шаги (не запрошены):

1. Деплой v3.45.8 на Wispbyte + Telegram smoke
2. ЮKassa — скриншоты по [yookassa-submission-pack.md](../guides/yookassa-submission-pack.md)
3. Фаза 3 автора (если появится в планах) — пока не описана
4. Прочие roadmap — см. [improvements-plan-2026-06.md](../plans/improvements-plan-2026-06.md), [product-audit-2026.md](../plans/product-audit-2026.md)

## История коммитов (релизная волна)

```
b942b21 fix: убрать неиспользуемый импорт tip_thank_you_keyboard (ruff F401)
c368e9e feat: автор в продукте фаза 2 — /status, Stars-кнопки, smoke_author · v3.45.8
1d0dcaf feat: polish author UX — кнопки после тура, компактная карточка · v3.45.7
02ccb0d feat: автор в продукте — made-by, что нового, контакт · v3.45.6
```

## Prompt для нового агента

```
Проект: bot_reminder (Telegram-бот напоминаний).
Прочитай docs/handoff/agent-context-2026-06-02.md — там текущее состояние.
Версия v3.45.8, 576 тестов, CI green, релиз опубликован.
Линия «Автор в продукте» завершена. Отвечай на русском.
Коммиты — только по явной просьбе.
```
