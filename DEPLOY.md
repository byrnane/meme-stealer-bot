# Deploy to a VPS

The bot uses Telegram long polling. It does not listen on a public port, so it can
run on the same VPS as websites, VPNs, and proxies.

Recommended available capacity:

- 1 CPU core;
- at least 512 MB free RAM;
- at least 1 GB free disk space;
- outbound HTTPS access to `api.telegram.org:443`.

Only one running instance may use the same `BOT_TOKEN`.

## Check the VPS

Run these commands before deployment:

```bash
free -h
df -h
docker --version
docker compose version
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

No inbound firewall port needs to be opened for the bot.

## First deployment

The example below uses `/opt/meme-stealer-bot`:

```bash
sudo mkdir -p /opt/meme-stealer-bot
sudo chown "$USER":"$USER" /opt/meme-stealer-bot
git clone <repository-url> /opt/meme-stealer-bot
cd /opt/meme-stealer-bot
cp .env.example .env
nano .env
bash scripts/deploy.sh
docker compose logs --tail=100 -f bot
```

Keep `.env` only on the server. Do not commit it.

## GitHub Actions deployment

Pushes to `main` run tests and deploy to the production VPS. The workflow needs
these values in the `production` GitHub environment:

Secrets:

- `DEPLOY_SSH_KEY`;
- `BOT_TOKEN`;
- `OWNER_ID`.

Variables:

- `DEPLOY_HOST`;
- `DEPLOY_PORT`;
- `DEPLOY_USER`;
- `DEPLOY_HOST_KEY_FINGERPRINT`;
- `LOG_LEVEL`.

The VPS uses a dedicated `meme-deploy` user and a hardened systemd service. The
user can upload releases and restart only `meme-stealer-bot.service`; it does
not have general root or Docker access.

The workflow creates the server `.env` from the GitHub Environment values on
every deployment. After changing a secret or variable, manually run the
`Deploy` workflow to apply it.

## Update

```bash
cd /opt/meme-stealer-bot
git pull --ff-only
bash scripts/deploy.sh
docker compose logs --tail=100 bot
```

## Backup

For the GitHub Actions deployment, the SQLite database is stored in
`/home/meme-deploy/app/shared/data/bot.sqlite3`. Create a consistent backup:

```bash
sudo -u meme-deploy /home/meme-deploy/app/current/.venv/bin/python -c \
  "import sqlite3; src=sqlite3.connect('/home/meme-deploy/app/shared/data/bot.sqlite3'); dst=sqlite3.connect('/home/meme-deploy/app/shared/data/bot.backup.sqlite3'); src.backup(dst); dst.close(); src.close()"
```

## Useful commands

```bash
docker compose ps
docker compose logs --tail=100 -f bot
docker compose restart bot
docker compose down
```

The Compose project has the fixed name `meme-stealer-bot`, so its container and
network names do not collide with other Compose projects on the VPS.
