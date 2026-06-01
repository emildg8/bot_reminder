# План улучшений · июнь 2026

Приоритет: impact × effort. Выполнение — волнами без лишних мелких релизов.

## Оценка текущего состояния (v3.42.2)

| Область | Оценка | Комментарий |
|---------|--------|-------------|
| NLP / время | 9/10 | HHMM, ambiguous, голос — закрыто |
| Группы / collective | 10/10 | assignee, inline ✏️🗑 своих |
| Admin | 10/10 | audit + broadcast draft в БД |
| Pro / Stars | 9/10 | код готов; включение на проде — ops |
| Тесты | 9/10 | 457 тестов, gate 65% |
| CI | 10/10 | green v3.42.2; release = lint CI |
| Docs | 9/10 | phase2 закрыт, postgres-backup |
| Ops | 7/10 | Wispbyte — ручной чеклист (волна J) |

**Phase 2:** [improvements-plan-phase2.md](improvements-plan-phase2.md)

## Фаза F — Admin UX ✅ v3.40

| # | Задача | Статус |
|---|--------|--------|
| F1 | `/adminmode`, user-test, `admin_tools_enabled` | ✅ v3.40.0 |
| F2 | Панель, broadcast, userinfo, adminlog | ✅ v3.40.0 |
| F3 | CI/Docker polish | ✅ v3.40.2–3.40.3 |

---

## Фаза F1 — Стабильность и группы ✅ v3.38

| # | Задача | Статус |
|---|--------|--------|
| F1.1 | `/delete` + `/del` в группах | ✅ v3.37.3 |
| F1.2 | `/edit N` без фразы, `#N` | ✅ v3.37.3 |
| F1.3 | Тесты delete/edit/pause/help | ✅ v3.38 |
| F1.4 | CI: deploy skip при отсутствии secrets (не красить весь workflow) | ✅ v3.38 |
| F1.5 | README + collective hint `/delete` | ✅ v3.38 |

## Фаза F2 — Тесты и качество (v3.38)

| # | Задача | Статус |
|---|--------|--------|
| F2.1 | `test_008_group_manage.py` — pause, delete deny, help | ✅ v3.38 |
| F2.2 | `test_reminder_delete.py` — сервис ошибок | ✅ v3.38 |
| F2.3 | Collective list hint содержит `/delete` | ✅ v3.38 |
| F2.4 | Coverage gate 56% | ✅ v3.38 |
| F2.5 | Coverage gate 65%, quality-metrics | ✅ v3.39 (22ca2a9) |

## Фаза F3.0 — Напоминание на участника ✅ v3.39

| # | Задача | Статус |
|---|--------|--------|
| F3.0.1 | @user + reply + голос | ✅ v3.39.0 |
| F3.0.2 | Confirm/created/list с «кому» | ✅ v3.39.0 |
| F3.0.3 | `docs/guides/group-assignee.md` | ✅ v3.39.0 |
| F3.0.4 | `/delete N yes`, list hint 👤 | ✅ v3.39.1 |
| F3.0.5 | Тесты + release workflow | ✅ v3.39.1 |

### Definition of Done — assignee (F3.0) ✅

- [x] Создание: @, reply, голос+reply
- [x] Редактирование с новым @
- [x] Confirm / created / collective notice с «кому»
- [x] `/list` 👤, срабатывание `format_reminder_message`
- [x] Гайд + ops smoke + 15+ тестов
- [x] CI green, релизы v3.39.0 / v3.39.1

## Фаза F3 — Продукт (backlog)

| # | Задача | Effort |
|---|--------|--------|
| F3.2 | Inline ✏️🗑 в группе только для своих | M | ✅ v3.41 |
| F3.3 | Telegram Stars / Pro | L | ✅ v3.42 |
| F3.4 | pg_dump для PostgreSQL | M | ✅ v3.42 |
| F3.5 | Guided onboarding v2 (повторный тур) | S | ✅ v3.41 |

## Фаза F4 — Ops (ручное)

| # | Задача |
|---|--------|
| F4.1 | GitHub Secrets: BOT_TOKEN, ADMIN, Wisp |
| F4.2 | Wispbyte: `bash start.sh`, GROQ_API_KEY |
| F4.3 | BotFather Group Privacy off |
| F4.4 | Smoke: `/ping`, assignee, `/list`, `/delete` — [ops-checklist](../guides/ops-checklist.md) |

---

## Правила релизов (после v1.0)

1. Один логический блок = одна версия (не +2% coverage отдельно).
2. Gate coverage: +3–5% за квартал, не каждый PR.
3. Обязательно: `verify_ops`, ruff, pytest, обновить `docs/v1.0-final-status.md` на major.
4. Синхронизация docs: [doc-maintenance.md](../guides/doc-maintenance.md).

## Definition of Done (F1–F2)

- [x] План задокументирован
- [x] CI lint-and-test green
- [x] Deploy не ломает workflow без secrets
- [x] Групповые команды покрыты тестами
- [x] README и help актуальны
