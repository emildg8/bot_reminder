# План улучшений · phase 2 (после v3.40)

**Актуально:** v3.41.0 · **413** тестов · CI green

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

## Волна H — v3.42 (продукт)

| # | Задача | Effort | Зачем |
|---|--------|--------|-------|
| H1 | F3.3 Telegram Stars / Pro | L | Монетизация (`monetization_enabled`) |
| H2 | F3.4 pg_dump cron + ops doc | M | PostgreSQL profile |
| H3 | Admin audit → БД (не in-memory) | M | Несколько админов, рестарт |
| H4 | Broadcast: персистентный черновик | S | Рестарт не теряет превью |

## Волна I — v3.43 (качество)

| # | Задача | Effort |
|---|--------|--------|
| I1 | Coverage scheduler / reminder_history (+3%) | M |
| I2 | pre-commit: verify_ops или pytest subset | S |
| I3 | Smoke e2e admin panel в CI | S |
| I4 | Карта admin-тестов в quality-metrics | S |

## Волна J — Ops (ручное + автomation)

| # | Задача | См. |
|---|--------|-----|
| J1 | GitHub Secrets полный набор | F4.1 |
| J2 | Wispbyte smoke v3.41 | [ops-checklist.md](../guides/ops-checklist.md) |
| J3 | BotFather Group Privacy | F4.3 |
| J4 | `/ping` → v3.41 на проде | v1.0-status |

---

## Закрыто в v3.40.x

| Фаза | Содержание |
|------|------------|
| F — Admin | `/adminmode`, панель, broadcast, userinfo, adminlog |
| CI fix | patched_db, coverage, `format_admin_stats` tuple |
| Docker | Alembic в образе |

## Definition of Done (волна G)

- [x] F3.2: кнопки в групповом `/list` только для `created_by == viewer`
- [x] F3.5: `onb:restart` + тест
- [x] Release CI = lint CI (verify_ops + cov)
- [x] `verify_ops` OK, pytest green
- [x] CHANGELOG + release note v3.41.0

## Правила

1. Не поднимать coverage gate без +3% фактического покрытия.
2. Release note обязателен **до** тега (`docs/releases/vX.Y.Z.md`).
3. Обновлять [improvements-plan-2026-06.md](improvements-plan-2026-06.md) и [v1.0-final-status.md](../v1.0-final-status.md) на minor.
