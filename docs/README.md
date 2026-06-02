# Документация bot_reminder

Оглавление проекта **v3.45.2** · [v1.0 финальный статус](v1.0-final-status.md)

## Начало работы

| Документ | Для кого |
|----------|----------|
| [../README.md](../README.md) | Обзор, установка, команды |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Разработчики |
| [../.github/DEPLOY.md](../.github/DEPLOY.md) | Деплой Wispbyte / CI |
| [../.env.example](../.env.example) | Все переменные окружения |

## Руководства

| Документ | Тема |
|----------|------|
| [guides/groups-and-channels.md](guides/groups-and-channels.md) | Группы, каналы, Group Privacy |
| [guides/ops-checklist.md](guides/ops-checklist.md) | Чеклист после деплоя |
| [guides/group-assignee.md](guides/group-assignee.md) | Напоминание на участника (@user, reply) |
| [guides/nlp-time-priority.md](guides/nlp-time-priority.md) | Приоритеты: «сегодня» + «через N минут» |
| [guides/stars-tips.md](guides/stars-tips.md) | Благодарность автору Stars |
| [guides/yookassa-submission-pack.md](guides/yookassa-submission-pack.md) | Тексты для анкеты ЮKassa (Stars `/thanks`) |
| [guides/quality-metrics.md](guides/quality-metrics.md) | Тесты (558), coverage 65%, ruff, verify_ops |
| [guides/doc-maintenance.md](guides/doc-maintenance.md) | Чеклист: версия, тесты, gate, help |
| [guides/admin-mode.md](guides/admin-mode.md) | Режим администратора / пользователя |
| [guides/postgres-backup.md](guides/postgres-backup.md) | Бэкап PostgreSQL, cron |

## Планы и аудит

| Документ | Тема |
|----------|------|
| [v1.0-final-status.md](v1.0-final-status.md) | **Финальный статус v1.0** — проверки, ops |
| [plans/product-audit-2026.md](plans/product-audit-2026.md) | Оценка продукта, roadmap A–E + F3.0 |
| [plans/improvements-roadmap.md](plans/improvements-roadmap.md) | Roadmap улучшений v3.16+ |
| [plans/improvements-plan-phase2.md](plans/improvements-plan-phase2.md) | План после v3.40 (волны G–J) |
| [plans/groups-channels.md](plans/groups-channels.md) | Архитектура collective |
| [plans/groups-phase5-ux.md](plans/groups-phase5-ux.md) | UX групп (фаза 5) |
| [plans/stars-tips-polish.md](plans/stars-tips-polish.md) | **Stars tips → prod** (P0–P3, волна M) |

## Релизы

- [../CHANGELOG.md](../CHANGELOG.md) — полная история
- [releases/](releases/) — заметки по версиям
- [releases/v3.45.2.md](releases/v3.45.2.md) — **текущий:** assignee кнопками + quality gate
- [releases/v3.45.0.md](releases/v3.45.0.md) — группы: выбор «Кому?» кнопками
- [releases/v3.44.8.md](releases/v3.44.8.md) — группы: auto-pick, edited_message, превью
- [releases/v3.44.7.md](releases/v3.44.7.md) — группы: варианты assignee + clean punctuation
- [releases/v3.44.4.md](releases/v3.44.4.md) — Stars passthrough + deploy check
- [releases/v3.44.0.md](releases/v3.44.0.md) — Stars tips prod-ready
- [releases/v3.43.0.md](releases/v3.43.0.md) — Stars: благодарность автору
- [releases/v3.42.2.md](releases/v3.42.2.md) — NLP «в 2 дня», strip_day для расписаний
- [releases/v3.42.0.md](releases/v3.42.0.md) — Stars, audit DB, broadcast draft
- [releases/feature-group-assignee.md](releases/feature-group-assignee.md) — ✅ assignee (F3.0) закрыт

Старые patch-релизы v3.44.x / v3.43.x — в [releases/](releases/) и [CHANGELOG.md](../CHANGELOG.md).

## CI / GitHub

| Файл | Назначение |
|------|------------|
| [../.github/workflows/ci.yml](../.github/workflows/ci.yml) | Lint, test, deploy |
| [../.github/workflows/release.yml](../.github/workflows/release.yml) | GitHub Release |
| [../.github/dependabot.yml](../.github/dependabot.yml) | Обновление зависимостей |
