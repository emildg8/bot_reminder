# Handoff · 2026-06-03

## Проект

- **Репо:** `d:\Dev\Telegram\bot_reminder` · GitHub `emildg8/bot_reminder`
- **Бот:** `@break_remind_bot`
- **Версия:** **v3.46.0** · **587** тестов

## Завершено: assignee display name в группах

Линия закрыта релизом **v3.46.0**. План: [group-assignee-v2.md](../plans/group-assignee-v2.md)

### Код

- `mention_parse.py` — UTF-16 entities, caption_entities, text_mention, plain name fallback
- `collective_confirm.py` — reply в группе, retry hint, метрика `group_hint_failure_count()`
- `create_confirm.py` / `edit.py` — fallback reply если hint не ушёл
- `messages.py` — display name в UI, welcome, parse fail hint

### Документация

- `group-assignee.md`, `groups-and-channels.md`, `ops-checklist.md`
- `CHANGELOG`, `docs/releases/v3.46.0.md`

## Ручной пост-деплой (Wispbyte)

См. [ops-checklist.md](../guides/ops-checklist.md) § Assignee v3.46:

1. `/ping` → v3.46.0
2. `@break_remind_bot` + **тап по участнику** + `через 1 мин тест` → reply `👌 👤 …`
3. Confirm в личке → создать → тег при срабатывании

## Проверки

```bash
python scripts/verify_ops.py
python scripts/smoke_group_mentions.py
pytest tests/test_mention_parse.py tests/test_006_collective_handlers.py -q
```
