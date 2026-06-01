# Roadmap улучшений (аудит v3.18)

Аудит с точки зрения пользователя, ops и тестов. Приоритет — impact × effort.

## Сделано

| # | Улучшение | Версия |
|---|-----------|--------|
| 1 | Group-меню compact + edit navigation | v3.16 |
| 2 | Group Privacy подсказки + admin warning | v3.16.1 |
| 3 | Callback reliability (early answer, error handler) | v3.17 |
| 4 | Group menu dedup, parse fail hints, /health privacy | v3.18 |
| 5 | Права бота fail-closed, DM deep link, reply→menu | v3.19 |
| 6 | Collective notice errors → лог + DM создателю | v3.19 |
| 7 | Авто-alarm админу при repair scheduler | v3.19 |
| 8 | Тесты chat_permissions, collective list | v3.19 |
| 9 | Группы без inline-меню | v3.19.1 |
| 10 | NLP: уточнение «завтра в 2» кнопками | v3.20 |
| 11 | Удалён мёртвый код group_* keyboards | v3.20 |
| 12 | NLP: «завтра созвон» → кнопки времени | v3.21 |
| 13 | Repository unit tests | v3.21 |
| 14 | E2E confirm → create → schedule (мок) | v3.21 |
| 15 | LLM fallback integration tests | v3.21 |
| 16 | Coverage gate в CI | v3.21 |
| 17 | «завтра в 2» — только день/ночь (без 09:00) | v3.22 |
| 18 | Уточнение времени при редактировании | v3.22 |
| 19 | /cancel сбрасывает pending-уточнение | v3.23 |
| 20 | Edit-сессия при ambiguous-кнопках | v3.23 |
| 21 | «напомни …» / «в два» для ambiguous | v3.23 |
| 22 | «созвон завтра в 2» (суффикс дня) | v3.24 |
| 23 | Подсказка при тексте вместо кнопки ambiguous | v3.24 |
| 24 | Тесты ambiguous_prompt | v3.24 |
| 25 | Handler tests callbacks (confirm/edit/done) | v3.25 |
| 26 | Snooze/delete handler tests | v3.26 |
| 27 | Coverage gate 40% | v3.26 |
| 28 | del_cancel + snooze ± handler tests | v3.27 |
| 29 | Coverage gate 42% | v3.27 |
| 30 | snooze preset/back handler tests | v3.28 |
| 31 | Coverage gate 45% | v3.28 |
| 32 | menu/list handler tests | v3.29 |
| 33 | Coverage gate 47% | v3.29 |
| 34 | menu:search/more + search:page tests | v3.30 |
| 35 | Coverage gate 50% | v3.30 |
| 36 | menu:help/about + send_search_results E2E | v3.31 |
| 37 | Coverage gate 52% | v3.31 |
| 38 | menu:examples/status/timezone handler tests | v3.32 |
| 39 | Coverage gate 55%, handler callback roadmap ✅ | v3.32 |
| 40 | Fix main/admin imports + smoke tests | v3.33 |
| 41 | Edit/settings handler tests | v3.33 |
| 42 | Product audit + plan to v1.0 | v3.33 |
| 43 | Documentation refresh (README, guides, GitHub) | v3.34 |
| 44 | Phases B–D + Pro MVP, v1.0-ready | v3.35 |
| 45 | Monetization off by default | v3.35.1 |
| 46 | Guided onboarding, privacy UX, edit hints | v3.36 |
| 47 | Alembic, PostgreSQL, Groq-only STT | v3.37 |
| 48 | /delete, /edit N в группах | v3.37.3 |
| 49 | План F1–F2, CI deploy skip, тесты групп | v3.38 |
| 50 | **Assignee:** @user, reply, голос; confirm/list/fire; `/delete yes` | v3.39.1 ✅ |
| 51 | Coverage gate **65%**, quality-metrics, doc-maintenance | v3.39.1 ✅ |
| 52 | `verify_ops` doc metrics, help tests, 377 tests | v3.39.2 ✅ |

## Дальше (backlog)

См. [improvements-plan-2026-06.md](improvements-plan-2026-06.md).

| # | Задача |
|---|--------|
| E4 | Telegram Stars оплата Pro |
| E5 | pg_dump backup для PostgreSQL |

## Отменено / не актуально

| # | Улучшение | Причина |
|---|-----------|---------|
| D | Auto-delete group menu через 30 с | Inline-меню в группах убрано в v3.19.1 |

## Ops-критерии (не код)

- [ ] Wispbyte Startup = `bash start.sh`
- [ ] Dismiss «Missing Package bot»
- [ ] Group Privacy Turn off (рекомендуется)
