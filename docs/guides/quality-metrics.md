# Метрики качества (CI)

Кратко, что проверяется перед каждым merge в `main`.

## 587 тестов (pytest)

Автоматические сценарии: парсинг фраз, БД, callbacks, группы, удаление и т.д.

- Запуск: `pytest` или `make test`
- Падение любого теста = регрессия, CI красный
- Число растёт по мере новых фич (не цель сама по себе)

## Coverage gate 65%

**Покрытие кода** — какая доля строк в пакете `bot/` хотя бы раз выполнилась во время тестов.

| Термин | Значение |
|--------|----------|
| `--cov=bot` | Считаем только прод-код в `bot/` |
| `--cov-fail-under=65` | CI падает, если покрытие **ниже 65%** |
| Факт (~2026-06) | **~66%** строк (CI) |

Это **страховка от регрессий**, не оценка «идеального бота». Порог **65%** с v3.39 (ранее 56% в v3.38).

### Почему не 100%?

| Слой | Почему сложно |
|------|----------------|
| `bot/main.py`, polling | Точка входа, живёт на сервере |
| `scheduler.py` | Фоновые job’ы, время, Telegram API |
| `llm_parser.py`, STT | Внешние API (Groq, Yandex) |
| Handlers | Сотни веток UI и edge cases |

100% на всём `bot/` потребовало бы тысяч моков и хрупких тестов «ради галочки». В индустрии для таких ботов норма **65–85%** на бизнес-логике (`services/`, `nlp/`), а не на glue-коде.

Цель проекта: **осмысленные тесты** (см. CONTRIBUTING), gate — только нижняя граница.

## Ruff

Статический анализ Python: неиспользуемые импорты, очевидные баги (E, F, B).

```bash
ruff check bot tests
```

## verify_ops

Скрипт `scripts/verify_ops.py` — не тесты логики, а **чеклист деплоя**:

- есть `start.sh`, `alembic`, `docker-compose.yml`, ops-доки;
- `start.sh` запускает `python -m bot.main`;
- версия в `bot/version.py` = `pyproject.toml` и в `README.md` / `docs/README.md`;
- **число тестов** в docs = `pytest --collect-only` (`scripts/doc_metrics.py`);
- **smoke** (офлайн): `smoke_nlp.py`, `smoke_group_mentions.py`, `smoke_stars.py`, `smoke_author.py`;
- в `.env.example` дефолты для Wispbyte (например `LOCAL_WHISPER_ENABLED=false`).

```bash
python scripts/verify_ops.py
# → verify_ops OK · v3.46.0
```

## Локально как в CI

```bash
ruff check bot tests
python scripts/verify_ops.py
pytest -v --cov=bot --cov-fail-under=65
```

## Карта тестов (587)

| Категория | Примеры файлов | ~кол-во |
|-----------|----------------|---------|
| NLP / время | `test_nlp_time_priority`, `test_absolute_time_parse`, `test_ambiguous_*`, `test_weekday_parse`, `test_rule_parser` | 100+ |
| DB / repo | `test_000_repository`, `test_db_migrate`, `test_duplicates` | 25+ |
| Callbacks / UI | `test_001`–`test_003`, `test_confirm_flow`, `test_pagination` | 60+ |
| Handlers | `test_004`–`test_008`, `test_005_handlers_core`, `test_007_onboarding` | 50+ |
| Collective / группы | `test_006_collective_handlers`, `test_008_group_manage`, `test_collective_*` | 40+ |
| Assignee / mention | `test_mention_*`, `test_assignee_*`, `test_create_assignee_raw` | 30+ |
| Scheduler / STT | `test_scheduler_*`, `test_media_stt`, `test_llm_*` | 30+ |
| Инфра | `test_verify_ops`, `test_smoke_imports`, `test_config`, `test_version` | 15+ |
| NLP smoke | `scripts/smoke_nlp.py`, `test_nlp_time_priority` | 5 + 22 |

Точное число: `pytest --collect-only -q` → `N tests collected`.

### Assignee (F3.0 + v3.45)

| Файл | Фокус |
|------|--------|
| `test_mention_create.py` | @ vs reply, приоритет, голос |
| `test_mention_from_message.py` | entities, `command_prefix_length` |
| `test_mention_parse.py` | auto-pick, префиксы, candidates |
| `test_mention_assignee_text.py` | confirm, created, list 👤 |
| `test_assignee_prompt.py` | кнопки, pending, should_offer |
| `test_assignee_callbacks.py` | callback `as:*` |
| `test_assignee_pick_note.py` | pick_note, превью, prompt |
| `test_collective_preview.py` | превью в группе |
| `test_create_assignee_raw.py` | голос → кандидаты из фразы |
| `test_006_collective_handlers.py` | `/remind`, multi-@ без времени |
| `test_reminder_display.py` | `tg://user?id=` в списке |
| `test_delete_command.py` | `/delete N yes` |

### Admin + Pro (v3.40–v3.42)

| Файл | Фокус |
|------|--------|
| `test_admin_mode.py` | `/adminmode`, кэш, меню |
| `test_admin_panel.py` | панель, broadcast, userinfo |
| `test_admin_panel_service.py` | stats, userfind, draft DB |
| `test_admin_audit.py` | журнал в БД |
| `test_admin_smoke.py` | smoke panel + log + broadcast (CI) |
| `test_stars_tips.py` | Stars tips, idempotency, pre_checkout |

## История coverage gate

| Версия | Gate | Комментарий |
|--------|------|-------------|
| v3.30–v3.31 | 50–52% | поэтапный рост |
| v3.32 | 55% | batch releases |
| v3.38 | 56% | F1–F2, групповые тесты |
| **v3.39+** | **65%** | quality-metrics, CI/Makefile |

## Roadmap покрытия

По плану `docs/plans/improvements-plan-2026-06.md`: +3–5% gate за квартал, не гнаться за 100% на весь репозиторий.

См. также [doc-maintenance.md](doc-maintenance.md) — что обновлять при релизе.
