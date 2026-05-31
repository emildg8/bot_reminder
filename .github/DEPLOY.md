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

**Не используй** `pip install && python -m bot.main` без `git pull` — код на диске не обновится, auto-update не поможет если бот не стартует.

### Wispbyte: «Missing Package Detected: bot»

Панель видит `python -m bot.main` и думает, что нужен пакет **`bot` с PyPI**. Это **ложное** срабатывание — `bot/` это код проекта.

| Кнопка | Действие |
|--------|----------|
| **Dismiss** | ✅ Закрыть, ничего не менять |
| **Add to Startup** | ❌ Не нажимать — добавит `pip install bot` и сломает деплой |

Startup Command должен быть **`bash start.sh`**, не `pip install bot`.

## Застрял на старой/бroken версии (IndentationError, SyntaxError)

1. **Console** в панели Wispbyte:
   ```bash
   cd /home/container && git pull origin main && bash start.sh
   ```
2. Или смени **Startup Command** на `bash start.sh` и нажми **Restart**.

После pull должна быть **v3.15.2+** (`grep __version__ bot/version.py`).

## Проверка

1. `gh secret list -R emildg8/bot_reminder` — 5 secrets
2. Push в `main` → Actions → **Deploy to Wispbyte** — restart + Telegram
3. `/ping` → актуальная версия

## Ручной деплой

```bash
gh workflow run CI -R emildg8/bot_reminder --ref main
```

На сервере (админ): `/update`
