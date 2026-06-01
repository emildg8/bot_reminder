# Feature complete: напоминание на участника группы

**Закрыто:** v3.39.1 · **Гайд:** [group-assignee.md](../guides/group-assignee.md)

## Версии

| Версия | Содержание |
|--------|------------|
| v3.39.0 | @user, reply, голос; `mention_create`; confirm/created/list |
| v3.39.1 | `/delete N yes`; list hints; release CI idempotent |
| docs | Финализация F3.0, ops smoke, DoD |

## Scope (включено)

- Создание с назначением: `/remind`, @бот+@user, reply, голос+reply
- Редактирование с новым @
- UI: confirm, «Готово», уведомление в группе, `/list` 👤
- Срабатывание: `format_reminder_message` с тегом
- Проверка: участник в чате (`mention_resolve`)
- Тесты: `test_mention_*`, `test_delete_command`, collective handlers (см. [quality-metrics.md](../guides/quality-metrics.md#assignee-f30))
- Документация: [doc-maintenance.md](../guides/doc-maintenance.md) для будущих релизов

## Out of scope (backlog)

- Несколько участников на одно напоминание
- Снятие assignee через `/edit` без пересоздания
- Inline-кнопки в группе (F3.2)

## Smoke после деплоя

См. чеклист в [group-assignee.md](../guides/group-assignee.md#чеклист-smoke-после-деплоя).
