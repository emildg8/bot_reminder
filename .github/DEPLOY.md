# Деплой bot_reminder

Автоматический pipeline: **push `main` → CI (lint + test) → restart Wispbyte → `start.sh`**.

---

## 1. Быстрая настройка (один раз)

```powershell
# Windows
copy .env.deploy.local.example .env.deploy.local
# Заполни BOT_TOKEN, ADMIN_TELEGRAM_IDS, WISP_*

.\scripts\setup_github_deploy.ps1
```

```bash
# Linux / macOS
cp .env.deploy.local.example .env.deploy.local
bash scripts/setup_github_deploy.sh
```

### GitHub Secrets

| Secret | Где взять | Обязательно |
|--------|-----------|-------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather), тот же что на сервере | ✅ |
| `ADMIN_TELEGRAM_IDS` | Telegram user id (`@userinfobot`) | ✅ |
| `WISP_PANEL_URL` | `https://panel.wispbyte.com` | для instant restart |
| `WISP_API_TOKEN` | Wispbyte → Account → Security → API Tokens | для instant restart |
| `WISP_SERVER_UUID` | UUID сервера из URL панели | для instant restart |

Альтернативные имена (Pterodactyl): `PTERODACTYL_PANEL_URL`, `PTERODACTYL_API_TOKEN`, `PTERODACTYL_SERVER_UUID`.

Проверка:

```bash
gh secret list -R emildg8/bot_reminder
```

---

## 2. Wispbyte

### Startup Command

```bash
bash start.sh
```

**Не используй** `pip install && python -m bot.main` без `git pull` — код на диске не обновится.

### «Missing Package Detected: bot»

Панель видит `python -m bot.main` и предлагает `pip install bot` с PyPI. Это **ложное** срабатывание — `bot/` это код проекта.

| Кнопка | Действие |
|--------|----------|
| **Dismiss** | ✅ Закрыть |
| **Add to Startup** | ❌ Сломает деплой |

### Переменные на сервере

Минимум в `.env` или Environment Variables панели:

```
BOT_TOKEN=...
GROQ_API_KEY=...          # рекомендуется
DEFAULT_TIMEZONE=Europe/Moscow
```

---

## 3. Без Wisp API

Если Wisp-secrets не заданы:

- CI шлёт уведомление в Telegram (если есть `BOT_TOKEN` + `ADMIN_TELEGRAM_IDS`)
- Бот сам проверяет GitHub **каждую 1 мин** (`AUTO_UPDATE_ENABLED=true`)
- Или вручную: **Restart** в панели → `start.sh` → `git pull`

---

## 4. BotFather: Group Privacy

| Симптом | Решение |
|---------|---------|
| `@бот …` молчит в группе | BotFather → Group Privacy → **Turn off** |
| `/remind@бот …` работает всегда | Рекомендуемый способ в группах |

Проверка: `/sysinfo` → строка Group Privacy.

---

## 5. Проверка деплоя

1. Push в `main` → [Actions](https://github.com/emildg8/bot_reminder/actions) → зелёный CI
2. Telegram: «🚀 Deploy …» / «Restart отправлен»
3. Бот: `/ping` → актуальная версия
4. Чеклист: [docs/guides/ops-checklist.md](../docs/guides/ops-checklist.md)

---

## 6. Ручной деплой / откат

```bash
# Перезапуск через GitHub Actions
gh workflow run CI -R emildg8/bot_reminder --ref main

# На сервере (Console Wispbyte)
cd /home/container && git pull origin main && bash start.sh

# Откат версии
git log -1 --oneline
git checkout <sha> && bash start.sh
```

В Telegram (админ): `/update` — pull с GitHub + restart.

---

## 7. Docker (альтернатива Wispbyte)

```bash
cp .env.example .env
docker compose up -d --build
```

См. [README.md](../README.md#docker).

---

## 8. Troubleshooting

| Проблема | Решение |
|----------|---------|
| IndentationError / SyntaxError после deploy | `git pull origin main && bash start.sh` |
| Бот не стартует | Console: `grep __version__ bot/version.py`, проверь `BOT_TOKEN` |
| CI deploy failed — secrets missing | `setup_github_deploy.ps1` |
| Старая версия после push | Restart в панели или подожди auto-update ~1 мин |
| Crash loop | v3.15.2+ auto-clear instance lock; проверь логи `data/logs/bot.log` |
