# Ops-чеклист

Выполни один раз после деплоя или смены сервера.

## Проверка репозитория (локально / CI)

```bash
make verify
# или: python scripts/verify_ops.py
```

## Wispbyte / VPS

- [ ] **Startup command:** `bash start.sh` (не `pip install bot`!)
- [ ] Dismiss «Missing Package bot» → **не** Add to Startup
- [ ] `.env` на сервере: `BOT_TOKEN`, при необходимости `GROQ_API_KEY`
- [ ] `data/` доступна для записи (SQLite, logs, backups)

## GitHub Actions

- [ ] Secrets: `BOT_TOKEN`, `ADMIN_TELEGRAM_IDS`
- [ ] Опционально Wisp: `WISP_PANEL_URL`, `WISP_API_TOKEN`, `WISP_SERVER_UUID`
- [ ] `gh secret list -R emildg8/bot_reminder` — минимум 2 secrets
- [ ] Push в `main` → Actions зелёный → Telegram «Deploy…»

## BotFather

- [ ] Group Privacy **Turn off** (если нужен `@бот` в группах)
- [ ] Команды бота актуальны (обновляются при старте)

## Проверка после деплоя

- [ ] `/ping` → `✅ Бот работает · v3.35.0 · …`
- [ ] `/sysinfo` → ffmpeg/STT/deploy sha
- [ ] Личка: «через 5 минут тест» → confirm → срабатывание
- [ ] Группа: `/remind@бот через 10 минут тест` → confirm в личку

## Мониторинг

- `/health` (админ) — scheduler, БД, repair
- Логи: `data/logs/bot.log`
- Бэкапы: `data/backups/` (авто каждые 24 ч)

## Откат

```bash
python scripts/restore_db.py data/backups/reminders_YYYYMMDD_HHMMSS.db
# на сервере:
cd /home/container && git checkout <sha> && bash start.sh
```
