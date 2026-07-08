#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if command -v uv >/dev/null 2>&1; then
  uv sync --extra dev
else
  python3 -m venv .venv
  . .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -e ".[dev]"
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created .env. Fill BOT_TOKEN and OWNER_ID."
else
  echo ".env already exists, left unchanged."
fi

. .venv/bin/activate
python -m meme_stealer_bot init-db

echo "Done. Fill .env and run: ./scripts/start.sh"
