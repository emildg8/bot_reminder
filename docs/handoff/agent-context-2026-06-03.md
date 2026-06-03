# Handoff · 2026-06-03

Скопируй в первое сообщение новому агенту или укажи: «прочитай `docs/handoff/agent-context-2026-06-03.md`».

## Проект

| Параметр | Значение |
|----------|----------|
| Репо | `d:\Dev\Telegram\bot_reminder` · GitHub `emildg8/bot_reminder` |
| Бот | `@break_remind_bot` |
| Версия | **v3.46.1** (`bot/version.py` = `pyproject.toml`) |
| Тесты | **589** (`pytest --collect-only -q`) |
| CI | green · Release [v3.46.1](https://github.com/emildg8/bot_reminder/releases/tag/v3.46.1) |
| HEAD | см. `git log -1` на `main` |

## Завершённая линия: assignee display name в группах

**Статус: ЗАКРЫТО** · v3.46.0 + v3.46.1 · план [group-assignee-v2.md](../plans/group-assignee-v2.md)

### Что сделано

| Область | Изменения |
|---------|-----------|
| Парсинг | UTF-16 entities, `caption_entities`, `text_mention`, plain name fallback |
| UX группы | reply `👌 👤 Emil · …`, retry hint, `group_hint_failure_count()` |
| UI | display name без `@` (`Emil` ≠ `@ivan`); welcome, `/remind`, gmenu |
| Тесты | +13 тестов (handlers, preview, UTF-16, caption) |

### Ключевые файлы

```
bot/services/mention_parse.py
bot/services/collective_confirm.py
bot/services/collective_preview.py
bot/services/create_confirm.py
bot/handlers/create.py
bot/texts/messages.py          # _looks_like_telegram_username()
docs/guides/group-assignee.md
docs/plans/group-assignee-v2.md
docs/releases/v3.46.0.md
docs/releases/v3.46.1.md
scripts/smoke_group_mentions.py
```

## Проверки

```bash
python scripts/verify_ops.py          # → verify_ops OK · v3.46.1
python scripts/smoke_group_mentions.py
pytest tests/test_mention_parse.py tests/test_006_collective_handlers.py \
       tests/test_collective_preview.py -q
```

## Ручной пост-деплoy (Wispbyte)

См. [ops-checklist.md](../guides/ops-checklist.md) § Assignee v3.46:

- [ ] `/ping` → **v3.46.1**
- [ ] `@break_remind_bot` + **тап по участнику** + `через 1 мин тест` → reply с **именем**
- [ ] Confirm → создать → тег при срабатывании

## Открытый backlog (не блокирует линию)

- P3: inline «Выберите участника» при ручном имени без entity ([group-assignee-v2.md](../plans/group-assignee-v2.md) §4.1)
- ЮKassa скриншоты — [yookassa-submission-pack.md](../guides/yookassa-submission-pack.md)

## Prompt для нового агента

```
Проект: bot_reminder (Telegram-бот напоминаний).
Прочитай docs/handoff/agent-context-2026-06-03.md.
Версия v3.46.1, 589 тестов, CI green.
Линия «@бот + display name в группах» ЗАКРЫТА. Отвечай на русском.
```
