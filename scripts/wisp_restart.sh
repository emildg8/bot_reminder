#!/bin/bash
# Перезапуск сервера Wispbyte/Wisp через Client API (вызывается из GitHub Actions).
set -euo pipefail

PANEL_URL="${WISP_PANEL_URL:-${PTERODACTYL_PANEL_URL:-}}"
API_TOKEN="${WISP_API_TOKEN:-${PTERODACTYL_API_TOKEN:-}}"
SERVER_UUID="${WISP_SERVER_UUID:-${PTERODACTYL_SERVER_UUID:-}}"

if [[ -z "$PANEL_URL" || -z "$API_TOKEN" || -z "$SERVER_UUID" ]]; then
  echo "Wisp/Pterodactyl secrets not configured — skip remote restart"
  echo "Bot will auto-update via GitHub polling within a few minutes."
  exit 0
fi

PANEL_URL="${PANEL_URL%/}"
ENDPOINT="${PANEL_URL}/api/client/servers/${SERVER_UUID}/power"

echo "==> Sending restart signal to ${PANEL_URL} (server ${SERVER_UUID:0:8}...)"

try_restart() {
  local accept_header="$1"
  HTTP_CODE=$(curl -sS -o /tmp/wisp_restart_body.txt -w "%{http_code}" -X POST "$ENDPOINT" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: ${accept_header}" \
    -d '{"signal":"restart"}' \
    --connect-timeout 15 \
    --max-time 120 || echo "000")
}

try_restart "application/vnd.wisp.v1+json"
if [[ "$HTTP_CODE" == "000" || "$HTTP_CODE" == "404" || "$HTTP_CODE" == "406" ]]; then
  echo "Retry with Pterodactyl Accept header..."
  try_restart "Application/vnd.pterodactyl.v1+json"
fi

echo "HTTP ${HTTP_CODE}"
if [[ -f /tmp/wisp_restart_body.txt ]]; then
  cat /tmp/wisp_restart_body.txt || true
  echo
fi

case "$HTTP_CODE" in
  200|201|204)
    echo "Restart accepted."
    exit 0
    ;;
  409)
    echo "Server already restarting — OK."
    exit 0
    ;;
  000|502|503|504)
    echo "::warning::Panel timeout or gateway error — restart may still be in progress."
    exit 0
    ;;
  *)
    echo "::error::Unexpected response from panel API."
    exit 1
    ;;
esac
