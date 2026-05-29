#!/bin/bash
# Деплой на Wispbyte / VPS: clone или pull, deps, run
set -euo pipefail

cd /home/container 2>/dev/null || cd "$(dirname "$0")/.." || true

if [ ! -f "bot/main.py" ]; then
  echo "==> Cloning from GitHub..."
  TMP_DIR=$(mktemp -d)
  git clone --depth 1 -b main https://github.com/emildg8/bot_reminder.git "$TMP_DIR"
  cp -r "$TMP_DIR"/. .
  rm -rf "$TMP_DIR"
fi

if [ -d .git ]; then
  echo "==> git pull"
  git pull origin main --ff-only || git pull origin main
fi

echo "==> pip install"
pip install -r requirements.txt -q

echo "==> Starting bot..."
exec python -m bot.main
