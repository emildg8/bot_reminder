# Метрики качества (CI)

Кратко, что проверяется перед каждым merge в `main`.

## 352 теста (pytest)

Автоматические сценарии: парсинг фраз, БД, callbacks, группы, удаление и т.д.

- Запуск: `pytest` или `make test`
- Падение любого теста = регрессия, CI красный
- Число растёт по мере новых фич (не цель сама по себе)

## Coverage gate 56% → 65%

**Покрытие кода** — какая доля строк в пакете `bot/` хотя бы раз выполнилась во время тестов.

| Термин | Значение |
|--------|----------|
| `--cov=bot` | Считаем только прод-код в `bot/` |
| `--cov-fail-under=65` | CI падает, если покрытие **ниже 65%** |
| Факт (~2026-06) | **~65%** строк (CI) |

Это **страховка от регрессий**, не оценка «идеального бота». Порог поднят с 56% до 65%, чтобы совпадать с реальным уровнем проекта.

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
- версия в `bot/version.py` = `pyproject.toml`;
- в `.env.example` дефолты для Wispbyte (например `LOCAL_WHISPER_ENABLED=false`).

```bash
python scripts/verify_ops.py
# → verify_ops OK · v3.38.0
```

## Локально как в CI

```bash
ruff check bot tests
python scripts/verify_ops.py
pytest -v --cov=bot --cov-fail-under=65
```

## Roadmap покрытия

По плану `docs/plans/improvements-plan-2026-06.md`: +3–5% gate за квартал, не гнаться за 100% на весь репозиторий.
