# Сопровождение документации

Чеклист при смене **версии**, **числа тестов** или **coverage gate**.

## Версия (`bot/version.py` = `pyproject.toml`)

| Файл | Что обновить |
|------|----------------|
| `CHANGELOG.md` | Секция `[X.Y.Z]` |
| `docs/releases/vX.Y.Z.md` | Release note |
| `docs/README.md` | Заголовок «Оглавление … vX.Y.Z» |
| `docs/v1.0-final-status.md` | Версия, дата, `/ping` в ops |
| `README.md` | Строка «Версия: vX.Y.Z» |
| `docs/guides/quality-metrics.md` | Пример `verify_ops OK · vX.Y.Z` |

`python scripts/verify_ops.py` падает, если версии в `version.py` и `pyproject.toml` расходятся.

## Тесты (после крупного PR с тестами)

```bash
make test-count          # сколько собрал pytest
python scripts/verify_ops.py   # сверит docs с collect (CI)
```

`verify_ops` сравнивает `pytest --collect-only` с шаблонами в [doc_metrics.py](../../scripts/doc_metrics.py). При расхождении обновите файлы ниже (одно и то же число):

Обновить число тестов (сейчас **572**, см. `make test-count`) в:

| Файл |
|------|
| `README.md` |
| `docs/v1.0-final-status.md` |
| `docs/guides/quality-metrics.md` |
| `docs/plans/improvements-plan-2026-06.md` (таблица оценки) |
| `docs/plans/product-audit-2026.md` §7 |

## Coverage gate

Источник правды: `.github/workflows/ci.yml`, `Makefile`, `CONTRIBUTING.md`, `pyproject` (если есть).

При смене порога обновить:

- `docs/guides/quality-metrics.md` — заголовок и таблица
- `README.md` — badge «Coverage ≥N%»
- `docs/plans/improvements-plan-2026-06.md` — строка F2.x
- **Не** переписывать исторические `docs/releases/v3.3*.md` (это хронология)

## Фича закрыта (как F3.0 assignee)

1. `docs/guides/<feature>.md` — гайд + smoke
2. `docs/releases/feature-*.md` — статус «закрыто»
3. `docs/plans/improvements-plan-2026-06.md` — фаза ✅ + DoD
4. `docs/v1.0-final-status.md` — строка в roadmap
5. `docs/guides/ops-checklist.md` — smoke-пункты
6. `CHANGELOG.md` + `docs/releases/vX.Y.Z.md`

## Help-тексты бота

При смене синтаксиса команд синхронизировать:

- `bot/texts/messages.py` — `HELP_TEXT_*`
- `bot/handlers/edit.py`, `manage.py` — подсказки ошибок
- `bot/services/onboarding.py` — примеры
- `tests/test_008_group_manage.py`, `test_texts_help_compat.py`, `test_doc_metrics.py`
- `scripts/doc_metrics.py` — шаблоны для `verify_ops`

## Major / v1.0 milestone

Обязательно обновить `docs/v1.0-final-status.md` и §7 в `product-audit-2026.md`.
