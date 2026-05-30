# Автоматический деплой (один раз настроить в GitHub)

После `git push` в `main`: **CI → тесты → перезапуск Wispbyte → `start.sh` (git pull + pip + run)**.

Локально ничего делать не нужно.

## GitHub Secrets

Репозиторий → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Обязательно | Описание |
|--------|-------------|----------|
| `BOT_TOKEN` | да | Токен бота (уже используется для avatar workflow) |
| `ADMIN_TELEGRAM_IDS` | да | ID админов через запятую, напр. `250891839` |
| `WISP_PANEL_URL` | для мгновенного деплоя | URL панели, напр. `https://panel.wispbyte.com` |
| `WISP_API_TOKEN` | для мгновенного деплоя | Client API token (Account → Security → API Tokens) |
| `WISP_SERVER_UUID` | для мгновенного деплоя | UUID сервера из URL панели |

Альтернативные имена (совместимость с Pterodactyl): `PTERODACTYL_PANEL_URL`, `PTERODACTYL_API_TOKEN`, `PTERODACTYL_SERVER_UUID`.

## Если Wisp-секреты не заданы

Бот сам проверяет GitHub каждые **3 минуты** и перезапускается при новом коммите (`AUTO_UPDATE_ENABLED=true` по умолчанию).  
На Wispbyte при выходе процесса панель поднимает его снова → `start.sh` делает `git pull`.

## Wispbyte startup command

```
bash start.sh
```

## Проверка

1. Push в `main`
2. GitHub Actions: job **Deploy to Wispbyte** — зелёный
3. Telegram: «Deploy … — перезапуск сервера…», затем «Бот запущен · v…»
