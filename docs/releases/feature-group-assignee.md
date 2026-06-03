# Feature complete · напоминание на участника группы

**Статус:** ✅ **ФИНАЛ** · prod smoke **2026-06-03** · релиз **v3.46.4**  
**Доработок по этой линии не планируется.**

| Документ | Назначение |
|----------|------------|
| [group-assignee.md](../guides/group-assignee.md) | Гайд для пользователей и ops |
| [group-assignee-v2.md](../plans/group-assignee-v2.md) | Техплан (архив, закрыт) |
| [v3.46.4.md](v3.46.4.md) | Последний релиз линии |

## Версии (v3.39 → v3.46.4)

| Версия | Содержание |
|--------|------------|
| v3.39.0–v3.39.1 | @user, reply, голос; `/delete N yes`; confirm/list |
| v3.44.8 | `edited_message`, `@бот` детект |
| v3.45.0+ | Кнопки «Кому?» при нескольких @ без времени |
| v3.46.0 | `text_mention`, UTF-16, reply в группе |
| v3.46.1 | Preview display name (`Emil` без `@`) |
| v3.46.2 | **Fix:** tips не перехватывал `@бот` → тишина |
| v3.46.3 | Срабатывание `⏰ Emil, тест`; `/ping` + Group Privacy |
| v3.46.4 | Pick при unresolved + `@` в фразе; `smoke_user_group_assignee` |

## Prod (подтверждено)

Фраза: `@break_remind_bot Emil Через 1 минуту тест` в группе «Болталка».

| Шаг | Результат |
|-----|-----------|
| Reply в группе | `👌 👤 Emil · через 1 мин …` |
| Confirm | `#35` · assignee Emil → `@emildg8` |
| Срабатывание | `⏰ Emil, тест` |

## Scope (включено)

- Создание: `/remind`, `@бот`+@user, `@бот`+**имя из списка**, reply, голос+caption
- Редактирование с новым @
- Collective: confirm в личке, reply `👌 …` в группе, `/list` 👤
- Срабатывание с display name / @username
- `mention_resolve` — участник в чате
- Тесты: `test_mention_*`, `test_collective_*`, `test_006_*`, `test_assignee_*`
- Smoke: `smoke_group_mentions`, `smoke_user_group_assignee` в `verify_ops`

## Out of scope (не будет)

| Тема | Причина |
|------|---------|
| Несколько assignee на одно напоминание | product |
| Снятие assignee через `/edit` | пересоздать напоминание |
| Resolve по имени без entity / @ | ограничение Bot API |
| Inline-меню создания в группе | by design — @ + личка |
| Picker «все участники чата» без @ в фразе | нет API search by name |

## Поддержка (не фича)

- **Group Privacy вкл** — ручной `@бот` не доходит; `/remind@бот` работает → [groups-and-channels.md](../guides/groups-and-channels.md)
- Имя **набранное с клавиатуры** без тапа из @ — предупреждение в confirm

## Проверки для регрессии

```bash
python scripts/verify_ops.py
python scripts/smoke_user_group_assignee.py
pytest tests/test_mention_create.py tests/test_006_collective_handlers.py -q
```
