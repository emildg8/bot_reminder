# Feature complete: напоминание на участника группы

**Закрыто:** v3.46.1 · **Гайд:** [group-assignee.md](../guides/group-assignee.md) · **План:** [group-assignee-v2.md](../plans/group-assignee-v2.md)

## Версии

| Версия | Содержание |
|--------|------------|
| v3.39.0 | @user, reply, голос; `mention_create`; confirm/created/list |
| v3.39.1 | `/delete N yes`; list hints; release CI idempotent |
| v3.44.8 | auto-pick nearest_time, edited_message, `@бот` детект |
| v3.45.0 | Кнопки «Кому?» при нескольких @ без времени |
| v3.46.0 | Display name (`text_mention`), UTF-16, caption_entities, reply в группе |
| v3.46.1 | Preview `Emil` без `@`; `_looks_like_telegram_username()` |

## Scope (включено)

- Создание: `/remind`, `@бот`+@user, `@бот`+**имя из списка**, reply, голос+caption
- Редактирование с новым @
- UI: confirm в личке, reply `👌 …` в группе, `/list` 👤
- Срабатывание: `format_reminder_message` с тегом
- Проверка: участник в чате (`mention_resolve`)
- Тесты: `test_mention_*`, `test_collective_*`, `test_006_collective_handlers`
- Smoke: `scripts/smoke_group_mentions.py` в `verify_ops`

## Out of scope (backlog)

- Несколько участников на одно напоминание
- Снятие assignee через `/edit` без пересоздания
- Inline-кнопки в группе (F3.2)
- Inline «Выберите участника» при ручном имени (P3)

## Smoke после деплоя

См. [group-assignee.md](../guides/group-assignee.md#чеклист-smoke-после-деплоя) и [ops-checklist.md](../guides/ops-checklist.md) § Assignee v3.46.
