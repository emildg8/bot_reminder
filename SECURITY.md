# Security Policy

## Поддерживаемые версии

| Версия | Поддержка |
|--------|-----------|
| latest `main` | ✅ |
| старше 2 минорных релизов | ❌ |

## Сообщить об уязвимости

**Не создавай публичный issue** для security-проблем.

1. Напиши maintainer через Telegram (admin бота) или private contact из профиля GitHub.
2. Опиши: шаги воспроизведения, impact, версию (`/ping` или `bot/version.py`).

Ожидаемый ответ: в течение 7 дней.

## Что считаем чувствительным

- `BOT_TOKEN`, API keys (Groq, OpenAI, Yandex)
- `ADMIN_TELEGRAM_IDS`
- `WISP_API_TOKEN`
- Содержимое `data/reminders.db` (личные напоминания пользователей)

## Рекомендации

- Не коммить `.env`, `.env.deploy.local`
- Ограничить `ADMIN_TELEGRAM_IDS` доверенными id
- На сервере: права на `data/` только для процесса бота
- Регулярные бэкапы: `make backup` / auto backup в `data/backups/`
