# План улучшений · phase 2 (после v3.40)

**Актуально:** v3.42.2 · **457** тестов · CI + Release green

Приоритет: impact × effort. Одна волна = один minor/patch релиз.

---

## Волна G — v3.41 ✅

| # | Задача | Effort | Статус |
|---|--------|--------|--------|
| G1 | F3.2: inline ✏️🗑 в группе для **своих** напоминаний | M | ✅ |
| G2 | F3.5: повторный тур «🎯 Тур по боту» в «⋯ Ещё» | S | ✅ |
| G3 | Release workflow: ruff + verify_ops + coverage 65% | S | ✅ |
| G4 | `doc-maintenance.md` — актуальные метрики | S | ✅ |
| G5 | `scripts/pg_backup.sh` — заготовка F3.4 | S | ✅ |

## Волна H — v3.42 ✅

| # | Задача | Effort | Статус |
|---|--------|--------|--------|
| H1 | F3.3 Telegram Stars / Pro | L | ✅ |
| H2 | F3.4 pg_dump cron + ops doc | M | ✅ |
| H3 | Admin audit → БД (не in-memory) | M | ✅ |
| H4 | Broadcast: персистентный черновик | S | ✅ |

## Волна I — v3.42 ✅

| # | Задача | Effort | Статус |
|---|--------|--------|--------|
| I1 | Coverage scheduler / reminder_history (+3%) | M | ✅ |
| I2 | pre-commit: verify_ops или pytest subset | S | ✅ |
| I3 | Smoke e2e admin panel в CI | S | ✅ |
| I4 | Карта admin-тестов в quality-metrics | S | ✅ |

## Волна K — NLP v3.42.2 ✅

| # | Задача | Статус |
|---|--------|--------|
| K1 | «завтра в 2 дня» → 14:00, задача без артефакта | ✅ |
| K2 | strip_day_words для interval/daily/weekly | ✅ |
| K3 | `test_nlp_time_priority.py` + `scripts/smoke_nlp.py` | ✅ |
| K4 | docs [nlp-time-priority.md](../guides/nlp-time-priority.md) | ✅ |

## Волна J — Ops (ручное на проде)

| # | Задача | Статус |
|---|--------|--------|
| J1 | GitHub Secrets: `BOT_TOKEN`, `ADMIN_TELEGRAM_IDS` | ✅ CI deploy notify |
| J2 | Wispbyte smoke v3.42.2 | 📋 [ops-checklist](../guides/ops-checklist.md) |
| J3 | BotFather Group Privacy + Stars | 📋 |
| J4 | `/ping` → v3.42.2 + `smoke_nlp.py` на сервере | 📋 |

---

## Закрыто в v3.40.x–v3.42

| Фаза | Содержание |
|------|------------|
| F — Admin | `/adminmode`, панель, broadcast, userinfo, adminlog |
| G — UX | inline ✏️🗑, тур, release CI |
| H — Pro/ops | Stars, audit/draft в БД, pg_backup doc |
| I — Quality | pre-commit verify_ops, smoke admin, coverage |
| K — NLP | «через N», «в 2 дня», test_nlp_time_priority, smoke_nlp |

## Definition of Done (волна K)

- [x] normalize_part_of_day + BARE_HOUR fix
- [x] `_schedule_task` / strip_day для расписаний
- [x] test_nlp_time_priority.py (457 тестов)
- [x] scripts/smoke_nlp.py + ops-checklist smoke table
- [x] CHANGELOG + release v3.42.2

## Definition of Done (волна H+I)

- [x] Stars: invoice, payment, pro_expires_at, idempotent charge_id
- [x] Admin audit + broadcast draft в БД (миграция 0003)
- [x] postgres-backup.md + cron
- [x] pre-commit verify_ops
- [x] test_admin_smoke, +15 тестов
- [x] CHANGELOG + release notes v3.42.0 / v3.42.1

## Правила

1. Не поднимать coverage gate без +3% фактического покрытия.
2. Release note обязателен **до** тега (`docs/releases/vX.Y.Z.md`).
3. Обновлять [improvements-plan-2026-06.md](improvements-plan-2026-06.md) и [v1.0-final-status.md](../v1.0-final-status.md) на minor.
