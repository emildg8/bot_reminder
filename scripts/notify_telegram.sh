#!/bin/bash
# Уведомление админов в Telegram (GitHub Actions deploy).
set -euo pipefail

TEXT="${1:-}"
if [[ -z "$TEXT" ]]; then
  echo "Usage: notify_telegram.sh <message>"
  exit 0
fi

if [[ -z "${BOT_TOKEN:-}" ]]; then
  echo "BOT_TOKEN not set — skip Telegram notify"
  exit 0
fi

ADMIN_IDS="${ADMIN_TELEGRAM_IDS:-}"
if [[ -z "$ADMIN_IDS" ]]; then
  echo "ADMIN_TELEGRAM_IDS not set — skip Telegram notify"
  exit 0
fi

IFS=',' read -ra IDS <<< "$ADMIN_IDS"
for raw_id in "${IDS[@]}"; do
  id="$(echo "$raw_id" | tr -d '[:space:]')"
  [[ -z "$id" ]] && continue
  curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${id}" \
    --data-urlencode "text=${TEXT}" \
    --data-urlencode "parse_mode=HTML" \
    || echo "Failed to notify admin ${id}"
done
