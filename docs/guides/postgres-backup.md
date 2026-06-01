# PostgreSQL — бэкапы

Для профиля `postgres` в `docker-compose.yml`.

## Ручной бэкап

```bash
bash scripts/pg_backup.sh
# или в каталог: bash scripts/pg_backup.sh /path/to/backups
```

Файл: `data/backups/pg_reminder_YYYYMMDD_HHMMSS.sql`

## Cron (VPS / хост)

```cron
# Ежедневно в 03:15 UTC
15 3 * * * cd /home/container && bash scripts/pg_backup.sh >> data/logs/pg_backup.log 2>&1
```

Перед cron убедись, что контейнер `db` запущен:

```bash
docker compose --profile postgres up -d db
```

## Ротация

Рекомендуется хранить 7–14 последних дампов (как `DB_BACKUP_KEEP` для SQLite):

```bash
find data/backups -name 'pg_reminder_*.sql' -mtime +14 -delete
```

## Восстановление

```bash
docker compose exec -T db psql -U reminder -d reminder < data/backups/pg_reminder_YYYYMMDD_HHMMSS.sql
```

После restore — перезапуск бота: `bash start.sh`

## Managed PostgreSQL

Если БД вне Docker — используй `pg_dump` провайдера или их snapshot API; переменная `DATABASE_URL=postgresql+asyncpg://...`

См. также [ops-checklist.md](ops-checklist.md)
