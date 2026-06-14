#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

command -v docker >/dev/null || {
  echo "Docker is not installed or is not available in PATH." >&2
  exit 1
}

docker compose version >/dev/null

if [[ ! -f .env ]]; then
  echo "Create .env from .env.example and fill BOT_TOKEN and OWNER_ID." >&2
  exit 1
fi

chmod 600 .env
mkdir -p data
docker compose config --quiet
docker compose build --pull
docker compose up -d --remove-orphans
docker compose ps
