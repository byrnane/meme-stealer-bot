#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Usage: deploy-meme-stealer-bot <git-sha>" >&2
  exit 2
fi

sha="$1"
archive="/home/meme-deploy/releases/${sha}.tar.gz"
app_root="/home/meme-deploy/app"
release="${app_root}/releases/${sha}"
shared="${app_root}/shared"
uv="/home/meme-deploy/bin/uv"
service="meme-stealer-bot.service"

if [[ ! -f "$archive" || -L "$archive" ]]; then
  echo "Release archive not found: $archive" >&2
  exit 1
fi

install -d -m 0755 "${app_root}/releases" "$release"
install -d -m 0700 "$shared" "${shared}/data"
tar -xzf "$archive" -C "$release" --no-same-owner --no-same-permissions
ln -sfn "${shared}/.env" "${release}/.env"
ln -sfn "${shared}/data" "${release}/data"

"$uv" venv --python 3.12 "${release}/.venv"
"$uv" pip install --python "${release}/.venv/bin/python" "$release"

previous="$(readlink -f "${app_root}/current" || true)"
ln -sfn "$release" "${app_root}/current"
if ! sudo /usr/bin/systemctl restart "$service"; then
  if [[ -n "$previous" ]]; then
    ln -sfn "$previous" "${app_root}/current"
    sudo /usr/bin/systemctl restart "$service"
  fi
  exit 1
fi

rm -f "$archive"
/usr/bin/systemctl --no-pager --full status "$service"
