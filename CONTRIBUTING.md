# Contributing

Спасибо за интерес к проекту! Краткие правила для разработки.

## Окружение

```bash
git clone https://github.com/emildg8/bot_reminder.git
cd bot_reminder
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Заполни `BOT_TOKEN` в `.env`.

## Перед PR

```bash
make lint          # ruff check bot tests
make verify        # ops + docs metrics (как в CI)
make test          # pytest, coverage ≥65%
make test-count    # только число тестов
```

Или вручную:

```bash
ruff check bot tests
pytest -v --cov=bot --cov-fail-under=65
```

## Стиль кода

- Python 3.11+, type hints где уместно
- **Ruff** (E, F, B) — конфиг в `pyproject.toml`
- Handlers — тонкие; логика в `bot/services/`
- Комментарии — только для неочевидной бизнес-логики
- Тесты — осмысленные сценарии, не ради coverage (см. [quality-metrics.md](docs/guides/quality-metrics.md))

## Структура тестов (~456)

Полная карта: [docs/guides/quality-metrics.md](docs/guides/quality-metrics.md).

| Файл | Назначение |
|------|------------|
| `tests/test_*_parse.py` | NLP unit tests |
| `tests/test_000_repository.py` | DB CRUD |
| `tests/test_001_callbacks_handlers.py` | confirm/edit/done |
| `tests/test_002_callbacks_snooze_delete.py` | snooze/delete |
| `tests/test_003_callbacks_menu_list.py` | menu/list/search |
| `tests/test_004_edit_settings_handlers.py` | edit/settings |
| `tests/test_005_handlers_core.py` | create text, manage |
| `tests/test_006_collective_handlers.py` | группы, `/remind`, assignee |
| `tests/test_007_onboarding_handlers.py` | onboarding |
| `tests/test_008_group_manage.py` | pause, delete, group help |
| `tests/test_mention_*.py` | @user, reply, entities |
| `tests/test_delete_command.py` | `/delete N yes` |
| `tests/test_reminder_delete.py` | сервис удаления |
| `tests/test_verify_ops.py` | чеклист деплоя |
| `tests/test_doc_metrics.py` | docs ↔ pytest count |
| `tests/test_admin_mode.py` | /adminmode admin/user |
| `tests/test_admin_panel.py` | /admin, userinfo, panel |
| `tests/test_smoke_imports.py` | wiring main/admin |
| `tests/callback_helpers.py` | `make_callback`, `make_bot`, `make_message` |
| `tests/db_helpers.py` | `patched_db` fixture |

Новые handler-тесты — через `patched_db` + мок Bot/CallbackQuery.

После добавления тестов: `pytest --collect-only -q` и обновить счётчик в README / [doc-maintenance.md](docs/guides/doc-maintenance.md).

## Версионирование

- Версия в `bot/version.py` и `pyproject.toml` (синхронно)
- Запись в `CHANGELOG.md` ([Keep a Changelog](https://keepachangelog.com/ru/1.1.0/))
- Release note: `docs/releases/vX.Y.Z.md`
- **Batch releases** — один релиз на логический блок, не на каждые 2 теста

## Коммиты

```
feat: новая возможность
fix: исправление бага
test: тесты
docs: документация
refactor: без изменения поведения
```

## Деплой

Push в `main` → CI → Wispbyte. См. [.github/DEPLOY.md](.github/DEPLOY.md).

## Вопросы

Issues: [github.com/emildg8/bot_reminder/issues](https://github.com/emildg8/bot_reminder/issues)
