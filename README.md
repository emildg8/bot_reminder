# Telegram-бот напоминалка

Бот-ежедневник для Telegram: напоминания текстом, голосом или кружочком (video note).

## Возможности

- **Разовые** напоминания: «через час выпить таблетки»
- **Интервальные**: «каждые 30 минут встать», «каждый час перерыв»
- **Ежедневные**: «каждый день в 9:00 зарядка»
- Ввод: текст, голосовое сообщение, кружочек
- Команды: `/start`, `/list`, `/timezone`
- Кнопки: подтверждение, отложить (+5/+15/+30 мин), готово, удалить

## Быстрый старт (локально)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # заполните BOT_TOKEN и ключи LLM
python -m bot.main
```

### Зависимости системы

- **ffmpeg** — для извлечения аудио из кружочков
- **Python 3.11+**

## Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | Бесплатный LLM ([console.groq.com](https://console.groq.com)) |
| `GEMINI_API_KEY` | Бесплатный LLM ([aistudio.google.com](https://aistudio.google.com)) |
| `OPENAI_API_KEY` | Опциональный fallback LLM |
| `WHISPER_MODEL` | `tiny` (быстро) или `base` (точнее) |
| `USE_YANDEX_STT` | `true` для Yandex SpeechKit fallback |
| `YANDEX_API_KEY` | API-ключ Yandex Cloud |
| `YANDEX_FOLDER_ID` | Folder ID Yandex Cloud |

## Парсинг напоминаний

Цепочка:

1. Бесплатный LLM (Groq → Gemini)
2. Правила + dateparser (русский)
3. OpenAI (если ключ задан)

## STT (голос и кружочки)

1. Локальный **faster-whisper** (модель скачивается при первом использовании)
2. Опционально **Yandex SpeechKit** (если `USE_YANDEX_STT=true`)

## Docker

```bash
copy .env.example .env
docker compose up --build -d
```

## Деплой на Wispbyte

1. Создайте бота в [@BotFather](https://t.me/BotFather), получите `BOT_TOKEN`
2. Залейте репозиторий на GitHub
3. На [Wispbyte](https://wispbyte.com) создайте Python-проект, подключите GitHub Pull
4. Startup command: `python -m bot.main`
5. Добавьте переменные окружения из `.env.example`
6. Рекомендации для free tier:
   - `WHISPER_MODEL=tiny`
   - Укажите хотя бы `GROQ_API_KEY` или `GEMINI_API_KEY`
   - Установите ffmpeg в startup script, если не доступен по умолчанию

Пример startup script:

```bash
apt-get update && apt-get install -y ffmpeg
pip install -r requirements.txt
python -m bot.main
```

## Примеры фраз

```
через 2 часа выпить таблетки
каждые 30 минут встать
каждый день в 9:00 зарядка
завтра в 10:00 встреча
```

## Структура

```
bot/
├── main.py              # точка входа
├── config.py            # настройки
├── handlers/            # команды и сообщения
├── services/
│   ├── nlp/             # LLM + rule parser
│   ├── stt/             # Whisper + Yandex
│   └── scheduler.py     # APScheduler
└── db/                  # SQLite модели
```
