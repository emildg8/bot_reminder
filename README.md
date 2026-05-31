# Telegram-бот напоминалка · v3.23

[![CI](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml/badge.svg)](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/emildg8/bot_reminder?label=release)](https://github.com/emildg8/bot_reminder/releases)

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком. Личка, группы и каналы.

> **v3.23** — /cancel сбрасывает уточнение; «напомни завтра в 2» / «завтра в два»; edit не теряется при кнопках.
>
> **v3.22** — «завтра в 2» только ☀️ 14:00 / 🌙 02:00; уточнение времени при редактировании.
>
> **v3.21** — roadmap закрыт: тесты repository/confirm/LLM, coverage gate, «завтра созвон» → кнопки времени.
>
> **v3.20** — «завтра в 2» → ☀️ 14:00 / 🌙 02:00.
>
> **v3.19.1** — в группах без inline-меню, только команды.
>
> **v3.19** — fail-closed права бота, DM-ссылка, health monitor для админов.
>
> **v3.18** — group-меню без дублей, parse fail с подсказкой `/remind@бот`.
>
> **v3.17** — надёжные callbacks в группах, `/sysinfo` с Group Privacy.
>
> **v3.16.1** — подсказки про Group Privacy: ручной @ не доходит, `/remind@бот` надёжнее.
>
> **v3.16** — компактное меню в группах: edit-in-place, без лишних экранов из лички.
>
> **v3.14** — разовые напоминания в канале через native Telegram schedule; подсказка для discussion group.
>
> **v3.13** — pause/clear/TZ из discussion group управляют каналом; единый /status.
>
> **v3.12** — расширенный /status, предупреждение о правах бота, resync linked chat.
>
> **v3.9** — единый UX для групп и каналов, scoped-команды, `/remind@бот`.

## Возможности

- **Разовые**: «через час», «через 3-4 часа», «через месяц», «завтра в 14:00», «15 июня в 10:00»
- **Интервальные**: «каждые 30 минут встать»
- **Ежедневные**: «каждый день в 9:00 зарядка»
- **По дням недели**: «по будням», «вт, ср, пт в 10:00 и 16:00» (несколько напоминаний)
- **Задача без времени** → кнопки +30 мин, +1 ч, +3 ч, +4 ч, завтра
- **Дневник** и **история за день** — события не удаляются
- **Статистика за месяц** — выполнено, срабатывания, отложения
- **Отложить** — счётчик − / + и быстрые варианты (настраиваются)
- **Группы и каналы**: `/remind@бот`; confirm в личку; срабатывание в чат/канал, кнопки в личке; pause/TZ — админы
- **Канал + обсуждения**: `/remind` из группы обсуждений публикует в канал

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/remind` | Создать напоминание в группе (`/remind@бот …`) |
| `/list` | Активные напоминания |
| `/history` | История за сегодня |
| `/journal` | Дневник дня |
| `/stats` | Статистика за месяц |
| `/settings` | Настройки «Отложить» |
| `/status` | Статус: кол-во, пауза, TZ |
| `/search` | Поиск по тексту |
| `/edit` | Изменить напоминание |
| `/cancel` | Выйти из режима |
| `/pause` / `/resume` | Пауза / возобновление |
| `/timezone` | Часовой пояс |
| `/clear` | Удалить все в чате |
| `/export` / `/import` | JSON |
| `/about` | О боте и возможностях |
| `/help` | Справка |
| `/ping` | Бот жив · версия · аптайм |
| `/health` | Состояние сервера + авто-перепланирование (админ) |
| `/update` | Обновление с GitHub + restart (админ) |
| `/sysinfo` | STT, ffmpeg, deploy sha (админ) |

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # Linux/macOS: cp .env.example .env
python -m bot.main
```

Нужен **ffmpeg** для локального Whisper; с **GROQ_API_KEY** голос и кружочки работают через облако без ffmpeg.

## Разработка

```bash
make install-dev
make test
make lint
make backup
make run
```

## Восстановление БД

```bash
python scripts/restore_db.py                  # последний бэкап из data/backups/
python scripts/restore_db.py data/backups/reminders_20260101_120000.db
```

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

## Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | Умный разбор фраз (опционально) |
| `DEFAULT_TIMEZONE` | По умолчанию `Europe/Moscow` |
| `ADMIN_TELEGRAM_IDS` | ID админов через запятую |

Полный список — в `.env.example`.

## Деплой — полностью автоматически

**Push в `main` → GitHub Actions (тесты + перезапуск Wispbyte) → `start.sh` на сервере.**

Один раз добавь secrets в GitHub — см. [.github/DEPLOY.md](.github/DEPLOY.md).

| Secret | Назначение |
|--------|------------|
| `BOT_TOKEN`, `ADMIN_TELEGRAM_IDS` | Уведомления о деплое |
| `WISP_PANEL_URL`, `WISP_API_TOKEN`, `WISP_SERVER_UUID` | Мгновенный restart через API |

**Startup command на Wispbyte:** `bash start.sh`

Без Wisp-секретов бот сам подтягивает обновления с GitHub каждую **1 мин** (auto-update) и при каждом старте.

**Первый раз:** `copy .env.deploy.local.example .env.deploy.local` → заполни → `.\scripts\setup_github_deploy.ps1`

---

**Репозиторий:** [github.com/emildg8/bot_reminder](https://github.com/emildg8/bot_reminder)
