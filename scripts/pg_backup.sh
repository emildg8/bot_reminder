#!/usr/bin/env bash
# PostgreSQL backup (docker compose --profile postgres).
# Usage: bash scripts/pg_backup.sh [output_dir]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/data/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="$OUT/pg_reminder_${STAMP}.sql"

mkdir -p "$OUT"

if ! docker compose ps db 2>/dev/null | grep -q "running"; then
  echo "PostgreSQL container 'db' is not running. Start: docker compose --profile postgres up -d db" >&2
  exit 1
fi

docker compose exec -T db pg_dump -U reminder -d reminder > "$FILE"
echo "Backup: $FILE"
