# План улучшений · июнь 2026

Приоритет: impact × effort. Выполнение — волнами без лишних мелких релизов.

## Оценка текущего состояния (v3.37.3)

| Область | Оценка | Комментарий |
|---------|--------|-------------|
| NLP / время | 9/10 | HHMM, ambiguous, голос — закрыто |
| Группы / collective | 9/10 | /remind, /delete, /edit N, privacy hints |
| Тесты | 8.5/10 | 340+ тестов, gate 55%; pause/export — слабее |
| CI | 8/10 | lint-and-test ✅; deploy падает без secrets |
| Docs | 9/10 | v1.0 status, guides, roadmap |
| Ops | 7/10 | Wispbyte — ручной чеклист |

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
| F2.4 | Coverage gate 56% (после +тестов) | ✅ v3.38 |

## Фаза F3 — Продукт (backlog)

| # | Задача | Effort |
|---|--------|--------|
| F3.1 | `/delete N yes` — без подтверждения | S |
| F3.2 | Inline ✏️🗑 в группе только для своих (опционально) | M |
| F3.3 | Telegram Stars / Pro | L |
| F3.4 | pg_dump для PostgreSQL | M |
| F3.5 | Guided onboarding v2 (повторный тур в /help) | S |

## Фаза F4 — Ops (ручное)

| # | Задача |
|---|--------|
| F4.1 | GitHub Secrets: BOT_TOKEN, ADMIN, Wisp |
| F4.2 | Wispbyte: `bash start.sh`, GROQ_API_KEY |
| F4.3 | BotFather Group Privacy off |
| F4.4 | Smoke: `/ping`, `/list`, `/delete` в группе |

---

## Правила релизов (после v1.0)

1. Один логический блок = одна версия (не +2% coverage отдельно).
2. Gate coverage: +3–5% за квартал, не каждый PR.
3. Обязательно: `verify_ops`, ruff, pytest, обновить `docs/v1.0-final-status.md` на major.

## Definition of Done (F1–F2)

- [x] План задокументирован
- [x] CI lint-and-test green
- [x] Deploy не ломает workflow без secrets
- [x] Групповые команды покрыты тестами
- [x] README и help актуальны
