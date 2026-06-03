# Ops-чеклист

Выполни один раз после деплоя или смены сервера.

## Проверка репозитория (локально / CI)

```bash
make verify
# verify_ops = файлы + версии + число тестов в docs + smoke_nlp + smoke_group_mentions + smoke_stars + smoke_author
python scripts/check_deploy.py   # версия + GitHub main (+ Telegram если BOT_TOKEN)
make migrate   # alembic upgrade head (на сервере — автоматически при старте бота)
```

## Wispbyte / VPS

- [ ] **Startup command:** `bash start.sh` (не `pip install bot`!)
- [ ] Dismiss «Missing Package bot» → **не** Add to Startup
- [ ] `.env` на сервере: `BOT_TOKEN`, **`GROQ_API_KEY`** (голос без local Whisper)
- [ ] `LOCAL_WHISPER_ENABLED=false` (по умолчанию)
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

- [ ] `/ping` → актуальная версия (**v3.46.0**)
- [ ] `/sysinfo` → STT: Groq (без Whisper local), deploy sha
- [ ] `python scripts/verify_ops.py` → `verify_ops OK · v3.46.0` (включает 4 smoke)
- [ ] Личка — NLP smoke (без «Уточни время»):

| Фраза | Ожидание |
|-------|----------|
| `сегодня через 1 минуту тест` | confirm +1 мин, задача «тест» |
| `завтра в 2 дня созвон` | confirm 14:00, задача «созвон» |
| `завтра каждые 2 часа встать` | interval, задача «встать» |

- [ ] Личка: «через 5 минут тест» → confirm → срабатывание
- [ ] Группа: `/remind@бот через 10 минут тест` → confirm в личку

### Напоминание на участника (F3.0)

См. [group-assignee.md](group-assignee.md)

- [ ] `/remind@бот @user через 10 минут тест` → в личке строка **👤 Кому**
- [ ] Ответ на чужое сообщение + `/remind@бот через 10 минут тест2` → **↩️ Кому**
- [ ] После срабатывания — тег участника в группе
- [ ] `/list` — 👤 у напоминания с назначением
- [ ] `/delete@бот N yes` — удаление без кнопки (подсказка в `/list`)

### Assignee v3.46 (display name)

- [ ] `@бот` + **тап по участнику** (имя без `@`) + `через 1 мин тест` → reply `👌 👤 Имя · …`
- [ ] Confirm в личке — ссылка на участника (tg://user?id=)

### Assignee v3.45 (несколько @ без времени)

- [ ] `@бот @user1 @user2 созвон` → **Кому напомнить?** + превью `📝 созвон` + кнопки
- [ ] Выбор `@user1` → confirm в личке с **👤 Кому**
- [ ] **Отмена** на клавиатуре → выбор сброшен
- [ ] `@бот @user1 @user2 через час созвон` → автовыбор (без кнопок) + confirm

## PostgreSQL (опционально)

```bash
# docker compose --profile postgres up -d
# DATABASE_URL=postgresql+asyncpg://reminder:reminder@db:5432/reminder
```

Бэкап SQLite: `data/backups/` (авто). PostgreSQL — [postgres-backup.md](postgres-backup.md) (`scripts/pg_backup.sh`, cron).

### Stars (v3.44+)

- [ ] BotFather → Payments → Telegram Stars
- [ ] `alembic upgrade head` — `20260604_0005` (`tip_nudge_at`), `20260604_0006` (`tip_nudge_dismissed_at`)
- [ ] `STARS_TIPS_ENABLED=true`
- [ ] `python scripts/smoke_stars.py` → OK
- [ ] `python scripts/smoke_author.py` → OK
- [ ] `/thanks` → invoice в **личку** → «Спасибо!»
- [ ] «Другая сумма» → число → confirm → invoice в личку
- [ ] «Другая сумма» → фраза с буквами → напоминание (не Stars)

## Мониторинг

- `/health` (админ) — scheduler, БД, repair
- Логи: `data/logs/bot.log`

## Откат

```bash
python scripts/restore_db.py data/backups/reminders_YYYYMMDD_HHMMSS.db
cd /home/container && git checkout <sha> && bash start.sh
```
