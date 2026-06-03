# Handoff · 2026-06-03

> Скопируй в первое сообщение новому агенту: «прочитай `docs/handoff/agent-context-2026-06-03.md`».

## Проект

| Параметр | Значение |
|----------|----------|
| Репо | `d:\Dev\Telegram\bot_reminder` · [GitHub](https://github.com/emildg8/bot_reminder) |
| Бот | `@break_remind_bot` |
| Версия | **v3.46.1** |
| Тесты | **589** |
| CI / Release | [v3.46.1](https://github.com/emildg8/bot_reminder/releases/tag/v3.46.1) |
| HEAD | `git log -1 --oneline` на `main`

## Завершённая линия: assignee display name в группах

**Статус: ЗАКРЫТО** · [group-assignee-v2.md](../plans/group-assignee-v2.md) · [feature-group-assignee.md](../releases/feature-group-assignee.md)

| Область | Изменения |
|---------|-----------|
| Парсинг | UTF-16 entities, `caption_entities`, `text_mention`, plain name fallback |
| UX группы | reply `👌 👤 Emil · …`, retry hint, `group_hint_failure_count()` |
| UI | display name без `@`; `_looks_like_telegram_username()` |
| Тесты | handlers, preview, UTF-16, caption (+13 к baseline) |

**Ключевой код:** `mention_parse.py`, `collective_confirm.py`, `collective_preview.py`, `messages.py`

## Проверки

```bash
python scripts/verify_ops.py
python scripts/smoke_group_mentions.py
pytest tests/test_mention_parse.py tests/test_006_collective_handlers.py \
       tests/test_collective_preview.py -q
```

## Ручной пост-деплой (Wispbyte)

[ops-checklist.md](../guides/ops-checklist.md) § Assignee v3.46:

- [ ] `/ping` → **v3.46.1**
- [ ] `@break_remind_bot` + **тап по участнику** + `через 1 мин тест` → reply с именем
- [ ] Confirm → создать → тег при срабатывании

## Backlog (не блокирует)

- P3: inline «Выберите участника» — [group-assignee-v2.md](../plans/group-assignee-v2.md) §4.1
- ЮKassa — [yookassa-submission-pack.md](../guides/yookassa-submission-pack.md)

## Prompt для нового агента

```
Проект: bot_reminder (Telegram-бот напоминаний).
Прочитай docs/handoff/agent-context-2026-06-03.md.
v3.46.1, 589 тестов, CI green. Линия assignee ЗАКРЫТА. Отвечай на русском.
```
