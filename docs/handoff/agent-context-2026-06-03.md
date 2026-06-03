# Handoff · 2026-06-03

> «Прочитай `docs/handoff/agent-context-2026-06-03.md`».

## Проект

| Параметр | Значение |
|----------|----------|
| Бот | `@break_remind_bot` |
| Версия | **v3.46.4** |
| Тесты | **597+** (см. `make test-count`) |
| CI / Release | tag `v3.46.4` после push |

## Assignee в группах — ЗАКРЫТО (код)

| Версия | Что |
|--------|-----|
| v3.46.0 | `text_mention`, UTF-16, reply в группе |
| v3.46.1 | preview `Emil` без `@` |
| v3.46.2 | **fix:** tips перехватывал `@бот` → тишина |
| v3.46.3 | срабатывание с именем; `/ping` + Group Privacy |
| v3.46.4 | assignee pick при unresolved + @ в фразе; `smoke_user_group_assignee` |

**Корневая причина тишины:** `tips.py` handler с тем же фильтром, что `create.py`, регистрировался раньше и делал `return` без ответа.

**Код:** `bot/handlers/filters.py` (`USER_PHRASE_TEXT`), `tip_custom_text_filter`, порядок роутеров в `main.py`.

## Prod smoke (ручной)

- [ ] `/ping` → v3.46.3 + `Group Privacy: выкл`
- [ ] `@break_remind_bot` + Emil из @ + `через 1 мин тест` → `👌 👤 Emil · …`
- [ ] Срабатывание → `⏰ Emil, тест` (не «участник»)

`/sysinfo` в user-mode не показывает privacy — используй `/ping` в группе.

## Проверки

```bash
python scripts/verify_ops.py
python scripts/smoke_user_group_assignee.py   # UX @бот + Emil без Telegram API
pytest tests/test_stars_tips.py tests/test_006_collective_handlers.py -q
```
