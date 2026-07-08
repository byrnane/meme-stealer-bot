#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -x .venv/bin/python ]]; then
  echo "Run ./scripts/setup.sh first." >&2
  exit 1
fi

. .venv/bin/activate
pytest -q
ruff check .
ruff format --check .
