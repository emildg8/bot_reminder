# Telegram-бот напоминалка

[![CI](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml/badge.svg)](https://github.com/emildg8/bot_reminder/actions/workflows/ci.yml)

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком. Работает в личке и в группах.

## Возможности

- **Разовые**: «через час выпить таблетки»
- **Интервальные**: «каждые 30 минут встать»
- **Ежедневные**: «каждый день в 9:00 зарядка»
- **По дням недели**: «по будням в 09:00», «пн ср пт в 10:00», «каждый понедельник в 9:00»
- Ввод: текст, голос, кружочек
- Меню команд и кнопки внизу чата
- Группы: напоминания в общий чат, `@username`; кнопки управления — в личку создателю
- **Редактирование**: `/edit 3 через 1 час новый текст` или кнопка ✏️ в `/list`
- `/export` и `/import` JSON (включая упоминания, отчёт об ошибках)
- Логи в файл с ротацией (~6 МБ)
- CI на GitHub Actions, Docker, авто-уведомление админов при старте/падении

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/list` | Список напоминаний |
| `/edit` | Изменить напоминание |
| `/menu` | Показать кнопки |
| `/timezone` | Часовой пояс |
| `/clear` | Удалить все в чате |
| `/export` | Скачать JSON |
| `/import` | Загрузить JSON |
| `/help` | Справка |
| `/ping` | Проверка работы |
| `/health` | Health-check (админ) |
| `/stats` | Статистика (админ) |

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
make install-dev   # или: pip install -r requirements-dev.txt
make test          # pytest
make lint          # ruff
make run           # запуск бота
```

## Docker

```bash
cp .env.example .env   # заполнить BOT_TOKEN
docker compose up -d --build
```

## Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | LLM ([console.groq.com](https://console.groq.com)) |
| `GEMINI_API_KEY` | LLM ([aistudio.google.com](https://aistudio.google.com)) |
| `OPENAI_API_KEY` | Опциональный fallback |
| `ADMIN_TELEGRAM_IDS` | ID админов: `250891839` или `111,222` |
| `WHISPER_MODEL` | `tiny` / `base` |
| `USE_YANDEX_STT` | `true` для Yandex SpeechKit |

## Парсинг

1. Правила + dateparser (быстро, без API)
2. Groq → Gemini (если ключи заданы)
3. OpenAI (опционально)

## Аватар бота

Файлы: `assets/bot_avatar.jpg` (640×640).

```bash
# один раз после деплоя или смены картинки
make avatar
# или
python scripts/set_bot_avatar.py
```

На Wispbyte аватар загружается **автоматически** при каждом старте (`start.sh` + `bot.main`).

Админ-команда: `/setavatar` — принудительно обновить аватар.

**GitHub Actions:** добавь секрет `BOT_TOKEN` в Settings → Secrets — аватар обновится при push в `assets/`.

## CI

На каждый push/PR в `main`: **ruff** + **pytest** (GitHub Actions).

## Логи

`data/logs/bot.log` (+ ротация). На Wispbyte: **Files** → `data/logs/`.

## Деплой на Wispbyte

Startup (рекомендуется):

```bash
bash start.sh
```

Или вручную:

```bash
cd /home/container && git pull origin main && pip install -r requirements.txt -q && python -m bot.main
```

Минимум в Environment: `BOT_TOKEN`, желательно `GROQ_API_KEY`, `ADMIN_TELEGRAM_IDS`.

## Примеры

```
через 30 минут тест
каждые 2 часа встать
каждый день в 9:00 зарядка
по будням в 09:00 стендап
пн ср пт в 10:00 тренировка
@username через 1 час задача
```
