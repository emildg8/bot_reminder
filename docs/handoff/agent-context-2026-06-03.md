# Handoff · 2026-06-03

> «Прочитай `docs/handoff/agent-context-2026-06-03.md`».

## Проект

| Параметр | Значение |
|----------|----------|
| Бот | `@break_remind_bot` |
| Версия | **v3.46.4** |
| Тесты | **597** (`make test-count`) |
| Release | [v3.46.4](https://github.com/emildg8/bot_reminder/releases/tag/v3.46.4) |

---

## Assignee в группах — ✅ ФИНАЛ (доработок нет)

**Prod smoke 2026-06-03:** `@break_remind_bot Emil Через 1 минуту тест` → reply `👌 👤 Emil` → `#35` → `⏰ Emil, тест`.

| Версия | Что |
|--------|-----|
| v3.46.0 | `text_mention`, UTF-16, reply в группе |
| v3.46.1 | preview `Emil` без `@` |
| v3.46.2 | tips перехватывал `@бот` → тишина (**корневая причина**) |
| v3.46.3 | срабатывание с именем; `/ping` + Group Privacy |
| v3.46.4 | pick unresolved + `@` в фразе; user smoke в CI |

**Код:** `filters.py` (`USER_PHRASE_TEXT`), `tips.tip_custom_text_filter`, `mention_parse.py`, `create.py`, `collective_confirm.py`.

**Документы:** [feature-group-assignee.md](../releases/feature-group-assignee.md) · [group-assignee.md](../guides/group-assignee.md).

---

## Следующая работа (вне assignee)

- [ЮKassa](../guides/yookassa-submission-pack.md) — подключение оплаты
- Обычный ops: Stars, Wispbyte checklist — [ops-checklist.md](../guides/ops-checklist.md)

---

## Проверки (регрессия assignee)

```bash
python scripts/verify_ops.py
python scripts/smoke_user_group_assignee.py
pytest tests/test_mention_create.py tests/test_006_collective_handlers.py -q
```

`/sysinfo` в user-mode не показывает privacy — в группе `/ping`.
