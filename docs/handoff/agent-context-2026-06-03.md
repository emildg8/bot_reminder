# Handoff · проект завершён

> «Прочитай `docs/PROJECT-COMPLETE.md`» · «Прочитай `docs/handoff/agent-context-2026-06-03.md`».

## Статус

| | |
|--|--|
| **Product** | ✅ **v1.0 готов** |
| **Код** | v3.46.4 · [release](https://github.com/emildg8/bot_reminder/releases/tag/v3.46.4) |
| **Тесты** | 597 · `verify_ops` OK |
| **Разработка** | **остановлена** до нового запроса |

## Prod (эталон)

`@break_remind_bot Emil Через 1 минуту тест` → `👌 👤 Emil` → #35 → `⏰ Emil, тест`

Assignee v3.46 — **ФИНАЛ**, доработок нет: [feature-group-assignee.md](../releases/feature-group-assignee.md).

## Не трогать без причины

- `mention_parse`, `tips`/`create` routing, `collective_confirm` — закрытая линия v3.46
- Версионирование 3.x — не переименовывать в 1.0.0 в `version.py` (v1.0 = продуктовый milestone)

## Вне кода (по желанию владельца)

- [yookassa-submission-pack.md](../guides/yookassa-submission-pack.md) — тексты анкеты (Stars уже в боте)
- [ops-checklist.md](../guides/ops-checklist.md) — при следующем деплое

## Регрессия (если меняете бот)

```bash
python scripts/verify_ops.py
make smoke-user-group
pytest -q
```
