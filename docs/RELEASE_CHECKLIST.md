# Release Checklist

Use this before making the repository public and before future releases.

## Repository state

- [ ] `git status --short` is clean or contains only intended release changes.
- [ ] `git ls-files` does not include `.env`, SQLite databases, dumps, backups, private keys, or local-only files.
- [ ] `git ls-files -o --exclude-standard` shows no ignored file that must be published.
- [ ] `gitleaks detect --redact --source .` passes on the full Git history.
- [ ] If a real Telegram bot token was ever committed, revoke it in BotFather and create a new token before publishing.

## Automated checks

- [ ] `uv lock --check`
- [ ] `pytest -q`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] Docker smoke:
  - [ ] `docker compose build --pull`
  - [ ] `docker compose run --rm bot id` prints a non-root UID.
  - [ ] `docker compose config --quiet`

## Manual Telegram smoke

- [ ] `/start` opens the main screen.
- [ ] `/settings` configures the target channel.
- [ ] Text -> meme -> preview -> publish posts once to the channel.
- [ ] Publishing error shows an alert and leaves the draft retryable.
- [ ] A non-owner user gets the private-bot response.
- [ ] Fast repeated publish clicks send only one channel post.

## Documentation

- [ ] README install and run commands are current for Windows, Linux, macOS, and Docker.
- [ ] `DEPLOY.md` still matches the production deploy workflow.
- [ ] `.env.example` lists every supported environment variable.
