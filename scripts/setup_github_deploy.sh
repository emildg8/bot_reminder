#!/bin/bash
# Одноразовая настройка GitHub Secrets для автодеплоя.
# cp .env.deploy.local.example .env.deploy.local  →  заполни  →  bash scripts/setup_github_deploy.sh
set -euo pipefail

ENV_FILE="${1:-.env.deploy.local}"
REPO="${GITHUB_REPO:-emildg8/bot_reminder}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

missing=()
for key in BOT_TOKEN ADMIN_TELEGRAM_IDS WISP_PANEL_URL WISP_API_TOKEN WISP_SERVER_UUID; do
  if [[ -z "${!key:-}" ]]; then
    missing+=("$key")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "Missing: ${missing[*]}"
  echo "Create $ENV_FILE from .env.deploy.local.example"
  exit 1
fi

gh auth status -h github.com

for key in BOT_TOKEN ADMIN_TELEGRAM_IDS WISP_PANEL_URL WISP_API_TOKEN WISP_SERVER_UUID; do
  echo "==> Setting secret $key"
  printf '%s' "${!key}" | gh secret set "$key" -R "$REPO" --body -
done

echo "Done. Test: gh workflow run CI -R $REPO --ref main"
