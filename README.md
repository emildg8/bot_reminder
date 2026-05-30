# Telegram-бот напоминалка · v2.6

[![CI](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml/badge.svg)](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml)

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком. Работает в личке и в группах.

> **v2.6.1** — auto-update теперь делает `git pull` + `pip install` и перезапускает процесс без ручного вмешательства.
>
> **v2.6.0** — полный CI/CD: push → тесты → auto-restart Wispbyte, fallback auto-update с GitHub.
>
> **v2.5.0** — optimistic advance для recurring, Docker healthcheck (heartbeat + pid + scheduler).
>
> **v2.4.0** — стабильность: no duplicate once after restart, graceful shutdown, safe backup, scheduler recovery.

## Возможности

- **Разовые**: «через час», «через неделю», «завтра в 14:00», «завтра созвон» (→ 9:00)
- **Интервальные**: «каждые 30 минут встать»
- **Ежедневные**: «каждый день в 9:00 зарядка», «ежедневно в 9:00»
- **По дням недели**: «по будням», «по выходным», «пт в 10:00», «пн ср пт»
- **Задача без времени** → кнопки «+30 мин», «+1 час», «Завтра 9:00/14:00»
- Ввод: текст, голос, кружочек
- Кнопки-примеры, карточка подтверждения, snooze (+5/+15/+30)
- Группы: `@username`, управление в ЛС; pause/clear/TZ — только админы
- Дубликаты: «Всё равно создать»; `/search` и кнопка 🔍 Поиск
- `/export` / `/import` JSON, автобэкап SQLite, restore-скрипт

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/list` | Список напоминаний |
| `/status` | Статус: кол-во, пауза, TZ |
| `/search` | Поиск по тексту (или кнопка 🔍) |
| `/edit` | Изменить напоминание |
| `/cancel` | Выйти из режима edit/search |
| `/pause` / `/resume` | Пауза / возобновление |
| `/timezone` | Часовой пояс |
| `/clear` | Удалить все в чате |
| `/export` / `/import` | JSON |
| `/help` | Справка |

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # Linux/macOS: cp .env.example .env
python -m bot.main
```

Нужен **ffmpeg** для кружочков.

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
| `GROQ_API_KEY` | LLM fallback (опционально) |
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
