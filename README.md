# Telegram-бот напоминалка · v3.4

[![CI](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml/badge.svg)](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/emildg8/bot_reminder?label=release)](https://github.com/emildg8/bot_reminder/releases)

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком. Работает в личке и в группах.

> **v3.4.0 — «к обеду», «к вечеру».** Разговорное время, показ распознанного текста при ошибке.
>
> **v3.3.0 — «через два часа» словами.** Аудиофайлы, Groq prompt, STT cleanup v3.
>
> **v3.2.0 — умное распознавание голоса.** Словесные часы, «два часа дня», «завтра утром», STT-cleanup.
>
> **v3.1.0 — голос и кружочки.** Groq Whisper STT, лимиты длины, ffmpeg в `start.sh`.
>
> **v3.0.0 — стабильный релиз.** Дневник, история, статистика, авто-деплой, полностью русский интерфейс.
>
> **v2.6.2** — исправлена аватарка: квадратный crop 640×640, авто-перезагрузка при смене файла.
>
> **v2.6.1** — auto-update теперь делает `git pull` + `pip install` и перезапускает процесс без ручного вмешательства.
>
> **v2.6.0** — полный CI/CD: push → тесты → auto-restart Wispbyte, fallback auto-update с GitHub.
>
> **v2.5.0** — optimistic advance для recurring, Docker healthcheck (heartbeat + pid + scheduler).
>
> **v2.4.0** — стабильность: no duplicate once after restart, graceful shutdown, safe backup, scheduler recovery.

## Возможности

- **Разовые**: «через час», «через 3-4 часа», «через пару часов», «завтра в 14:00»
- **Интервальные**: «каждые 30 минут встать»
- **Ежедневные**: «каждый день в 9:00 зарядка»
- **По дням недели**: «по будням», «по выходным», «пт в 10:00»
- **Задача без времени** → кнопки +30 мин, +1 ч, +3 ч, +4 ч, завтра
- **Дневник** и **история за день** — события не удаляются
- **Статистика за месяц** — выполнено, срабатывания, отложения
- **Отложить** — счётчик − / + и быстрые варианты (настраиваются)
- Группы: `@username`, управление в личке; pause/clear/TZ — только админы

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
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
| `/sysinfo` | Системная статистика (только админ бота) |

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

Без Wisp-секретов бот сам подтягивает обновления с GitHub каждые 3 мин (auto-update).

---

**Репозиторий:** [github.com/emildg8/bot_reminder](https://github.com/emildg8/bot_reminder)
