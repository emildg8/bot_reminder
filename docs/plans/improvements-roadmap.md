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

## Дальше (идеи)

| # | Улучшение | Impact | Effort |
|---|-----------|--------|--------|
| B | Поднять coverage gate постепенно | low | ongoing |

## Отменено / не актуально

| # | Улучшение | Причина |
|---|-----------|---------|
| D | Auto-delete group menu через 30 с | Inline-меню в группах убрано в v3.19.1 |

## Ops-критерии (не код)

- [ ] Wispbyte Startup = `bash start.sh`
- [ ] Dismiss «Missing Package bot»
- [ ] Group Privacy Turn off (рекомендуется)
