# Telegram-бот напоминалка

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком. Работает в личке и в группах.

## Возможности

- **Разовые**: «через час выпить таблетки»
- **Интервальные**: «каждые 30 минут встать»
- **Ежедневные**: «каждый день в 9:00 зарядка»
- **По дням недели**: «по будням в 09:00», «пн ср пт в 10:00», «каждый понедельник в 9:00»
- Ввод: текст, голос, кружочек
- Меню команд и кнопки внизу чата
- Группы: напоминания в общий чат, кнопки только у создателя
- `/export` и `/import` JSON для бэкапа
- Логи в файл с ротацией (~6 МБ)

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/list` | Список напоминаний |
| `/menu` | Показать кнопки |
| `/timezone` | Часовой пояс |
| `/clear` | Удалить все в чате |
| `/export` | Скачать JSON |
| `/import` | Загрузить JSON |
| `/help` | Справка |
| `/ping` | Проверка работы |
| `/stats` | Статистика (только админ) |

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m bot.main
```

Нужен **ffmpeg** для кружочков.

## Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | LLM ([console.groq.com](https://console.groq.com)) |
| `GEMINI_API_KEY` | LLM ([aistudio.google.com](https://aistudio.google.com)) |
| `OPENAI_API_KEY` | Опциональный fallback |
| `ADMIN_TELEGRAM_IDS` | ID админов: `250891839` или `111,222` |
| `WHISPER_MODEL` | `tiny` / `base` |

## Парсинг

1. Правила + dateparser (быстро, без API)
2. Groq → Gemini (если ключи заданы)
3. OpenAI (опционально)

## Логи

`data/logs/bot.log` (+ ротация). На Wispbyte: **Files** → `data/logs/`.

## Деплой на Wispbyte

Startup:

```bash
cd /home/container && git pull origin main 2>/dev/null; pip install -r requirements.txt -q && python -m bot.main
```

Минимум в Environment: `BOT_TOKEN`, желательно `GROQ_API_KEY`.

## Примеры

```
через 30 минут тест
каждые 2 часа встать
каждый день в 9:00 зарядка
по будням в 09:00 стендап
пн ср пт в 10:00 тренировка
```
