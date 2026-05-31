# Автоматический деплой (один раз настроить)

**Push в `main` → CI (тесты) → restart Wispbyte → `start.sh` (git pull + run).**

## Быстрая настройка (один раз)

```powershell
# 1. Скопируй шаблон и заполни значения
copy .env.deploy.local.example .env.deploy.local

# 2. Загрузи secrets в GitHub (нужен gh auth login)
.\scripts\setup_github_deploy.ps1
```

Linux/macOS: `cp .env.deploy.local.example .env.deploy.local` → `bash scripts/setup_github_deploy.sh`

| Secret | Где взять |
|--------|-----------|
| `BOT_TOKEN` | BotFather + тот же токен на Wispbyte |
| `ADMIN_TELEGRAM_IDS` | Telegram user id, напр. `250891839` |
| `WISP_PANEL_URL` | `https://panel.wispbyte.com` |
| `WISP_API_TOKEN` | Wispbyte → Account → Security → API Tokens |
| `WISP_SERVER_UUID` | UUID сервера из URL панели |

Альтернативные имена (Pterodactyl): `PTERODACTYL_PANEL_URL`, `PTERODACTYL_API_TOKEN`, `PTERODACTYL_SERVER_UUID`.

## Если Wisp API не настроен

При наличии `BOT_TOKEN` + `ADMIN_TELEGRAM_IDS` CI шлёт уведомление в Telegram.  
Бот сам проверяет GitHub **каждую минуту** и при старте — `git pull` + перезапуск (~1 мин после push).

## Wispbyte startup command

```
bash start.sh
```

## Проверка

1. `gh secret list -R emildg8/bot_reminder` — 5 secrets
2. Push в `main` → Actions → **Deploy to Wispbyte** — restart + Telegram
3. `/ping` → актуальная версия

## Ручной деплой

```bash
gh workflow run CI -R emildg8/bot_reminder --ref main
```

На сервере (админ): `/update`
