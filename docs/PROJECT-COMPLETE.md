# Проект завершён · Product v1.0

**Дата:** 2026-06-03 · **Версия кода:** [v3.46.4](releases/v3.46.4.md) · **Бот:** [@break_remind_bot](https://t.me/break_remind_bot)

Продукт **готов к эксплуатации**. Запланированный roadmap (A–L, assignee v3.46) **закрыт в коде и на prod**. Дальнейшая разработка — только по явному запросу (баги, регуляторика, новые фичи).

---

## Что входит в v1.0

| Область | Статус | Документ |
|---------|--------|----------|
| Напоминания (текст, голос, NLP) | ✅ | [README](../README.md) |
| Группы / каналы (collective) | ✅ | [groups-and-channels.md](guides/groups-and-channels.md) |
| Assignee в группах | ✅ **ФИНАЛ** | [feature-group-assignee.md](releases/feature-group-assignee.md) |
| Stars `/thanks` | ✅ | [stars-tips.md](guides/stars-tips.md) |
| Автор в продукте | ✅ | [author-presence.md](guides/author-presence.md) |
| Admin / audit / broadcast | ✅ | [admin-mode.md](guides/admin-mode.md) |
| CI + 597 тестов + 5 smoke | ✅ | [quality-metrics.md](guides/quality-metrics.md) |

---

## Prod (подтверждено)

| Сценарий | Результат |
|----------|-----------|
| `@break_remind_bot Emil Через 1 минуту тест` | reply → confirm #35 → `⏰ Emil, тест` |
| Group Privacy | выкл (ручной `@бот` работает) |

---

## Автоматические gate (всегда перед релизом)

```bash
ruff check bot tests
python -m pytest -q
python scripts/verify_ops.py
```

Ожидание: ruff OK · 597 passed · `verify_ops OK · v3.46.4`

---

## Не входит в v1.0 (осознанно)

| Тема | Примечание |
|------|------------|
| ЮKassa виджет на сайте | Оплата в боте — **Telegram Stars**; анкета — [yookassa-submission-pack.md](guides/yookassa-submission-pack.md) (вне кода) |
| Несколько assignee на напоминание | out of scope |
| e2e Stars testnet | опционально |
| Рост coverage >66% | не блокер |
| Inline-меню создания в группе | by design |

---

## Эксплуатация (не разработка)

Разовая настройка и регрессия при деплое — [ops-checklist.md](guides/ops-checklist.md).  
Сопровождение docs/версий — [doc-maintenance.md](guides/doc-maintenance.md).

---

## Handoff для агента

1. **Не** reopen assignee v3.46 без бага в prod.
2. Новые задачи — отдельная ветка/версия; начать с этого файла + [handoff/agent-context-2026-06-03.md](handoff/agent-context-2026-06-03.md).
3. Регрессия assignee: `make smoke-user-group`.

---

*Product v1.0 = релизная линия v3.46.4. Semver приложения остаётся 3.x.*
