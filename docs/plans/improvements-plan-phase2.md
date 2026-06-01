# План улучшений · phase 2 (после v3.40)

**Актуально:** v3.42.1 · **428** тестов · CI + Release green

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

## Волна J — Ops (ручное на проде)

| # | Задача | Статус |
|---|--------|--------|
| J1 | GitHub Secrets полный набор | 📋 [ops-checklist](../guides/ops-checklist.md) |
| J2 | Wispbyte smoke v3.42.1 | 📋 |
| J3 | BotFather Group Privacy + Stars | 📋 |
| J4 | `/ping` → v3.42.1 на проде | 📋 |

---

## Закрыто в v3.40.x–v3.42

| Фаза | Содержание |
|------|------------|
| F — Admin | `/adminmode`, панель, broadcast, userinfo, adminlog |
| G — UX | inline ✏️🗑, тур, release CI |
| H — Pro/ops | Stars, audit/draft в БД, pg_backup doc |
| I — Quality | pre-commit verify_ops, smoke admin, coverage |

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
