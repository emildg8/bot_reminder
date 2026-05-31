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

## Дальше (backlog)

| # | Улучшение | Impact | Effort |
|---|-----------|--------|--------|
| A | NLP: уточнение «завтра в 2» / дефолт 9:00 — кнопки | high | medium |
| B | E2E-тесты confirm → create → schedule (мок Bot) | medium | medium |
| C | Coverage gate в CI | low | small |
| D | Auto-delete group menu через 30 с | low | small |
| E | LLM fallback integration tests | low | medium |
| F | Repository unit tests | medium | medium |

## Ops-критерии (не код)

- [ ] Wispbyte Startup = `bash start.sh`
- [ ] Dismiss «Missing Package bot»
- [ ] Group Privacy Turn off (рекомендуется)
