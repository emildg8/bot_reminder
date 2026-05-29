#!/bin/bash
# Обходной деплой на Wispbyte, если GitHub Pull даёт "repository '.' does not exist"
set -e

cd /home/container 2>/dev/null || cd "$(dirname "$0")" || true

if [ ! -f "bot/main.py" ]; then
  echo "==> bot/main.py not found, cloning from GitHub..."
  TMP_DIR=$(mktemp -d)
  git clone --depth 1 -b main https://github.com/emildg8/bot_reminder.git "$TMP_DIR"
  cp -r "$TMP_DIR"/. .
  rm -rf "$TMP_DIR"
  echo "==> Clone done."
fi

echo "==> Installing dependencies..."
pip install -r requirements.txt -q

echo "==> Starting bot..."
exec python -m bot.main
