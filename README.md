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

## Логи

Пишутся в файл с ротацией (~6 МБ всего):

- `data/logs/bot.log` — текущий
- `data/logs/bot.log.1`, `bot.log.2` — архив

На Wispbyte: **Files** → `data/logs/` → скачать `bot.log` после падения (консоль панели логи не хранит).

Настройка в `.env`: `LOG_MAX_BYTES` (размер одного файла), `LOG_BACKUP_COUNT` (число архивов).

## Docker

```bash
copy .env.example .env
docker compose up --build -d
```

## Деплой на Wispbyte

1. Создайте бота в [@BotFather](https://t.me/BotFather), получите `BOT_TOKEN`
2. Репозиторий: https://github.com/emildg8/bot_reminder (ветка **`main`**)
3. На [Wispbyte](https://wispbyte.com) → **Repository Settings**

### Настройки репозитория (важно)

| Поле | Значение |
|------|----------|
| **Repository URL** | `https://github.com/emildg8/bot_reminder.git` |
| **Branch** | `main` |
| **GitHub Username** | оставить **пустым** (репозиторий публичный) |
| **Personal Access Token** | оставить **пустым** |

URL **обязательно** с `https://` и `.git` в конце.  
Вариант `github.com/emildg8/bot_reminder` без протокола на Wispbyte часто даёт ошибку:
`fatal: repository '.' does not exist`.

После ввода URL нажмите **Save**, затем **Clone**.

### Если Clone падает с `repository '.' does not exist` (баг Wispbyte)

Кнопка **Clone** на панели может не работать — git получает `.` вместо URL. Обходные варианты:

**Вариант A — одна команда в Startup (рекомендуется, сервер может быть пустым)**

В **Startup command** вставьте целиком:

```bash
cd /home/container && if [ ! -f bot/main.py ]; then TMP=$(mktemp -d) && git clone --depth 1 -b main https://github.com/emildg8/bot_reminder.git "$TMP" && cp -r "$TMP"/. . && rm -rf "$TMP"; fi && pip install -r requirements.txt -q && python -m bot.main
```

Запустите сервер — код скачается с GitHub при первом старте.

Если `start.sh` уже есть на сервере, можно короче: `bash start.sh`

**Вариант B — ручная загрузка**

1. Скачайте ZIP: https://github.com/emildg8/bot_reminder/archive/refs/heads/main.zip
2. Распакуйте в корень сервера через **File Manager** (должен быть `bot/main.py` в корне).
3. Startup command:
   ```bash
   pip install -r requirements.txt && python -m bot.main
   ```

**Вариант C — попробовать формат owner/repo**

В поле URL только: `emildg8/bot_reminder` (без `https://`) — у некоторых панелей так парсится.

### Startup command

Первый запуск (установка зависимостей):

```bash
pip install -r requirements.txt && python -m bot.main
```

С ffmpeg для кружочков:

```bash
apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt && python -m bot.main
```

### Переменные окружения

Минимум: `BOT_TOKEN`. Желательно: `GROQ_API_KEY` или `GEMINI_API_KEY`.

### Если Clone всё равно не работает

1. Очистите поля Username и Token, сохраните, Clone снова.
2. Создайте новый PAT на GitHub только с правом **public_repo** (или **Contents: Read** для fine-grained) и вставьте в Token, Username = `emildg8`.
3. Альтернатива: вручную загрузите файлы через File Manager Wispbyte (без Git), затем только `pip install` и startup.

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
