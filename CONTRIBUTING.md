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
make test          # pytest, coverage ≥65%
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

## Структура тестов

| Файл | Назначение |
|------|------------|
| `tests/test_*_parse.py` | NLP unit tests |
| `tests/test_000_repository.py` | DB CRUD |
| `tests/test_001_callbacks_handlers.py` | confirm/edit/done |
| `tests/test_002_callbacks_snooze_delete.py` | snooze/delete |
| `tests/test_003_callbacks_menu_list.py` | menu/list/search |
| `tests/test_004_edit_settings_handlers.py` | edit/settings |
| `tests/test_smoke_imports.py` | wiring main/admin |
| `tests/callback_helpers.py` | `make_callback`, `make_bot`, `make_message` |
| `tests/db_helpers.py` | `patched_db` fixture |

Новые handler-тесты — через `patched_db` + мок Bot/CallbackQuery.

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
