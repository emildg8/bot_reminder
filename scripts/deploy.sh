#!/bin/bash
# Production deploy: pull, deps, restart (Wispbyte / VPS)
set -euo pipefail

cd "$(dirname "$0")/.." || cd /home/container

echo "==> git pull"
if [[ -d .git ]]; then
  git pull origin main
else
  echo "Not a git repo — skip pull"
fi

echo "==> pip install"
pip install -r requirements.txt -q

echo "==> ready — restart bot process"
exec python -m bot.main
