# Напоминание на участника группы

**Статус:** ✅ готово · **v3.39.0–3.44.5** · код: `bot/services/mention_create.py`, `bot/services/mention_parse.py`

Назначьте, **кому** в группе придёт упоминание при срабатывании.

## Способы

| # | Как | Пример |
|---|-----|--------|
| 1 | `/remind` + @ из списка | `/remind@бот @ivan завтра в 14:00 созвон` |
| 2 | @бот + @user + фраза | `@бот @ivan через час задача` |
| 2b | компакт / разделители | `@бот@ivan …`, `@бот + @ivan …`, `@бот — @ivan …`, `@бот @ivan,задача` |
| 3 | **Ответ** на сообщение + `/remind` | ответ на Ивана → `/remind@бот завтра задача` |
| 4 | **Голос** + reply | ответ на сообщение → голос «завтра в 14:00 созвон» |

Приоритет: явный `@user` в тексте важнее, чем reply. Если в фразе **несколько** `@user` — назначается **первый** (слева направо), остальные убираются из текста напоминания.

## Важно

- **@ из списка Telegram** (тап по имени) — не набор с клавиатуры.
- Участник должен **быть в группе** — иначе в confirm будет предупреждение; при срабатывании тег может не сработать.
- Подтверждение — в **личке** с ботом (кнопки «Создать / Отмена»).

## Что видит пользователь

| Этап | UI |
|------|-----|
| Confirm (личка) | `👤 Кому: @ivan` или `↩️ … (ответ на сообщение)` |
| После создания | «Готово» + строка кому; в группе — краткое уведомление |
| `/list` | 👤 — кликабельная ссылка на участника |
| Срабатывание | `⏰ @ivan, **текст**` |

## Редактирование

`/edit 24 @petr завтра в 10:00 новый текст` — сменить время и адресата.

Если в правке **нет** @ и reply — **назначение не меняется** (остаётся прежний участник). Чтобы снять тег — удалите напоминание и создайте заново.

## Удаление

`/delete 24` — с кнопкой · `/delete 24 yes` — сразу (см. `/list` hint).

## Ограничения (by design)

- Только **один** участник на напоминание.
- В **канале** — назначение на участника не используется (публикация в канал).
- @, набранный вручную с клавиатуры, Telegram часто **не передаёт** боту — используйте список или `/remind`.

## Чеклист smoke (после деплоя)

- [ ] `make smoke-group-mentions` или `python scripts/smoke_group_mentions.py`
- [ ] `/ping` → ≥ v3.44.5
- [ ] `/remind@бот @user через 5 минут тест` → confirm с **Кому**
- [ ] `@бот@user через 5 минут` / `@бот + @user через 5 минут` → то же
- [ ] Ответ на сообщение + `/remind@бот через 5 минут тест2` → **↩️ Кому**
- [ ] После confirm — в группе срабатывание с тегом
- [ ] `/list` — у строки есть 👤

## Тесты (автоматические)

Ядро assignee — **21+** тестов в `test_mention_*`; плюс collective и delete.

| Файл | Что |
|------|-----|
| `tests/test_mention_create.py` | reply, @, приоритет, голос |
| `tests/test_mention_from_message.py` | entities после `/remind@бот` |
| `tests/test_mention_assignee_text.py` | confirm, created, collective notice |
| `tests/test_mention_resolve.py` | участник в чате |
| `tests/test_mention_parse.py` | разбор entity |
| `tests/test_006_collective_handlers.py` | `/remind` + reply в группе |
| `tests/test_reminder_display.py` | 👤 в `/list`, `tg://user?id=` |
| `tests/test_delete_command.py` | `/delete N yes` |
| `tests/test_004_edit_settings_handlers.py` | `/edit` с новым @ |

Запуск: `pytest tests/test_mention_create.py tests/test_mention_from_message.py -v`

## Связанные документы

- [groups-and-channels.md](groups-and-channels.md) — collective-режим
- [improvements-plan F3.0](../plans/improvements-plan-2026-06.md) — roadmap
- [quality-metrics.md](quality-metrics.md) — карта всех 460 тестов
