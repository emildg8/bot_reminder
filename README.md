# ⏰ Telegram-бот напоминалка

[![CI](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml/badge.svg)](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/emildg8/bot_reminder?label=release)](https://github.com/emildg8/bot_reminder/releases)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coverage ≥55%](https://img.shields.io/badge/coverage-≥55%25-green.svg)](.github/workflows/ci.yml)

**Версия:** [v3.35.1](CHANGELOG.md) · **322 теста** · **деплой:** push в `main` → CI → Wispbyte

Telegram-бот для напоминаний на русском языке: пиши текстом, надиктуй голосом или отправь кружочек — бот поймёт время и напомнит. Работает в личке, группах и каналах.

---

## Содержание

- [Возможности](#возможности)
- [Быстрый старт](#быстрый-старт)
- [Команды](#команды)
- [Группы и каналы](#группы-и-каналы)
- [Конфигурация](#конфигурация)
- [Разработка](#разработка)
- [Деплой](#деплой)
- [Документация](#документация)

---

## Возможности

| Область | Примеры |
|---------|---------|
| **Разовые** | «через час», «через 3–4 часа», «завтра в 14:00», «15 июня в 10:00» |
| **Интервалы** | «каждые 30 минут встать» |
| **Расписание** | «каждый день в 9:00», «по будням», «пн ср пт в 10:00» |
| **Без времени** | «созвон» → кнопки +30 мин / +1 ч / завтра |
| **Неоднозначное** | «завтра в 2» → ☀️ 14:00 или 🌙 02:00 |
| **Голос / кружок** | STT через Groq (или локальный Whisper + ffmpeg) |
| **Отложить** | picker − / +, быстрые presets, настройка в `/settings` |
| **Дневник** | `/journal`, история за день, статистика за месяц |
| **Collective** | группы и каналы: `/remind@бот`, confirm в личку, fire в чат |

**Стек:** Python 3.11+ · [aiogram 3](https://docs.aiogram.dev/) · SQLAlchemy · APScheduler · rule-based NLP + LLM fallback

---

## Быстрый старт

### Локально

```bash
git clone https://github.com/emildg8/bot_reminder.git
cd bot_reminder

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env   # Windows: copy .env.example .env
# Заполни BOT_TOKEN в .env

python -m bot.main
```

В Telegram: `/start` → напиши «через 30 минут выпить воды».

**Голос:** задай `GROQ_API_KEY` в `.env` — ffmpeg не обязателен. Без Groq нужен [ffmpeg](https://ffmpeg.org/) для локального Whisper.

### Docker

```bash
cp .env.example .env
# заполни BOT_TOKEN
docker compose up -d --build
docker compose logs -f bot
```

---

## Команды

### Пользовательские

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/list` | Активные напоминания |
| `/history` | История за сегодня |
| `/journal` | Дневник дня |
| `/stats` | Статистика за месяц |
| `/search` | Поиск по тексту |
| `/edit` | Изменить напоминание |
| `/settings` | Настройки «Отложить» |
| `/status` | Статус: кол-во, пауза, TZ |
| `/timezone` | Часовой пояс |
| `/pause` / `/resume` | Пауза / возобновление (админы в группах) |
| `/clear` | Удалить все напоминания в чате |
| `/export` / `/import` | Резервная копия JSON |
| `/help` | Справка |
| `/about` | О боте |
| `/subscribe` | Pro (зарезервировано, сейчас выкл.) |
| `/cancel` | Выйти из режима (поиск, edit, уточнение времени) |

### Группы

| Команда | Описание |
|---------|----------|
| `/remind@бот …` | Создать напоминание (надёжнее, чем `@бот` в личку) |

### Админ бота

| Команда | Описание |
|---------|----------|
| `/ping` | Бот жив · версия · аптайм |
| `/health` | Состояние сервера, repair scheduler |
| `/update` | Обновление с GitHub + restart |
| `/sysinfo` | STT, ffmpeg, deploy sha, Group Privacy |
| `/grantpro` | Выдать Pro (админ, когда включена монетизация) |

---

## Группы и каналы

```
Личка          → текст / голос → confirm → напоминание
Группа         → /remind@бот … → confirm в личку → fire в группу
Канал          → /remind@бот … → публикация в канал
Discussion grp → /remind из обсуждений → публикация в связанный канал
```

**Важно для групп**

1. **Group Privacy** в BotFather → **Turn off**, если нужен ручной `@бот` (иначе работает только `/remind@бот`).
2. В группах **нет inline-меню** — только команды и reply-кнопки в личке.
3. Кнопки «Готово» / «Отложить» в collective-режиме — в **личке** с ботом.

Подробнее: [docs/guides/groups-and-channels.md](docs/guides/groups-and-channels.md)

---

## Конфигурация

Скопируй `.env.example` → `.env`. Минимум:

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | ✅ | Токен от [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | рекомендуется | LLM + STT (голос без ffmpeg) |
| `DEFAULT_TIMEZONE` | — | По умолчанию `Europe/Moscow` |
| `ADMIN_TELEGRAM_IDS` | для деплоя | Telegram user id через запятую |

Полный список переменных — в [.env.example](.env.example).

**Данные:** SQLite в `data/reminders.db`, логи `data/logs/`, бэкапы `data/backups/`.

**Восстановление БД:**

```bash
python scripts/restore_db.py
python scripts/restore_db.py data/backups/reminders_YYYYMMDD_HHMMSS.db
```

---

## Разработка

```bash
make install-dev   # зависимости
make test          # pytest, coverage ≥55%
make lint          # ruff
make run           # python -m bot.main
make backup        # ручной бэкап БД
```

Структура проекта:

```
bot/
  handlers/     # aiogram routers (create, menu, callbacks, …)
  services/     # NLP, scheduler, drafts, collective UX
  db/           # models, repository
  keyboards/    # inline + reply
tests/          # unit + handler tests (308+)
scripts/        # deploy, backup, healthcheck
docs/           # guides, releases, plans
```

Как contribить: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Деплой

**Автоматически:** push в `main` → GitHub Actions (ruff + pytest) → restart Wispbyte → `start.sh`.

| Шаг | Действие |
|-----|----------|
| 1 | `cp .env.deploy.local.example .env.deploy.local` → заполни secrets |
| 2 | `.\scripts\setup_github_deploy.ps1` (или `.sh`) |
| 3 | Wispbyte **Startup command:** `bash start.sh` |
| 4 | Dismiss «Missing Package bot» (не Add to Startup!) |

Полная инструкция: [.github/DEPLOY.md](.github/DEPLOY.md)

Без Wisp API бот сам тянет обновления с GitHub каждую **1 мин** (`AUTO_UPDATE_ENABLED`).

---

## Документация

| Документ | Описание |
|----------|----------|
| [CHANGELOG.md](CHANGELOG.md) | История версий |
| [docs/README.md](docs/README.md) | Оглавление docs |
| [.github/DEPLOY.md](.github/DEPLOY.md) | Деплой и Wispbyte |
| [docs/plans/product-audit-2026.md](docs/plans/product-audit-2026.md) | Аудит продукта, roadmap до v1.0 |
| [docs/guides/groups-and-channels.md](docs/guides/groups-and-channels.md) | Группы, каналы, privacy |
| [docs/releases/](docs/releases/) | Release notes по версиям |

---

## Лицензия

MIT — см. [LICENSE](LICENSE).

**Репозиторий:** [github.com/emildg8/bot_reminder](https://github.com/emildg8/bot_reminder)
