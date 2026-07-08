# Meme Stealer Bot

| Русский | English |
| --- | --- |
| Личный Telegram-бот для чистой публикации мемов в свой канал. Принимает фото, GIF, видео и альбомы, убирает подпись/ссылку оригинала, добавляет твой комментарий и общую подпись, затем показывает превью или публикует сразу. | Personal Telegram bot for clean meme reposts into your own channel. It accepts photos, GIFs, videos, and albums, removes the original caption/source, adds your comment and shared signature, then shows a preview or publishes immediately. |
| Работает через long polling и SQLite. Публичный HTTP-порт, webhook и отдельная база не нужны. | Uses Telegram long polling and SQLite. No public HTTP port, webhook, or external database required. |
| Управление приватное: бот слушает только `OWNER_ID`. Нативное меню содержит `/start` и `/settings`, остальные экраны работают через inline-кнопки. | Owner-only control: the bot accepts commands only from `OWNER_ID`. Native menu has `/start` and `/settings`; other screens use inline buttons. |

## Быстрый старт / Quick Start

| Русский | English |
| --- | --- |
| 1. Создай бота через [@BotFather](https://t.me/BotFather). | 1. Create a bot with [@BotFather](https://t.me/BotFather). |
| 2. Узнай свой числовой Telegram ID. | 2. Find your numeric Telegram user ID. |
| 3. Добавь бота админом канала с правом публикации. | 3. Add the bot as a channel admin with posting rights. |
| 4. Скопируй `.env.example` в `.env` и заполни `BOT_TOKEN` / `OWNER_ID`. | 4. Copy `.env.example` to `.env` and fill `BOT_TOKEN` / `OWNER_ID`. |
| 5. Запусти локально или через Docker. | 5. Run locally or via Docker. |

### Windows

```powershell
.\scripts\setup.ps1
notepad .env
.\scripts\doctor.ps1
.\scripts\start.ps1
```

### Linux / macOS

```bash
bash scripts/setup.sh
nano .env
bash scripts/check.sh
bash scripts/start.sh
```

### Docker Compose

```bash
cp .env.example .env
nano .env
mkdir -p data
sudo chown -R 10001:10001 data
sudo chmod 700 data
docker compose up -d --build
docker compose logs -f bot
```

## Конфиг / Configuration

```env
BOT_TOKEN=123456:replace-me
OWNER_ID=123456789
DATABASE_PATH=data/bot.sqlite3
LOG_LEVEL=INFO
```

| Variable | Description |
| --- | --- |
| `BOT_TOKEN` | Telegram bot token from BotFather. |
| `OWNER_ID` | Numeric Telegram user ID allowed to control the bot. |
| `DATABASE_PATH` | SQLite path, default `data/bot.sqlite3`. |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

Не коммить `.env`, базы, дампы, бэкапы и приватные ключи.

Do not commit `.env`, databases, dumps, backups, or private keys.

## Использование / Usage

| Русский | English |
| --- | --- |
| Напиши боту `/start`, затем `/settings` и выбери канал. | Send `/start`, then `/settings`, and choose the target channel. |
| Отправь текст комментария, затем мем. | Send a comment text, then send or forward a meme. |
| Проверь превью и нажми `Опубликовать`, либо включи мгновенную публикацию в настройках. | Review the preview and press `Опубликовать`, or enable instant publishing in settings. |
| `/cancel` очищает ожидающий текст и текущий ввод. | `/cancel` clears pending text and the current input state. |

## Ссылки / Links

- [DEPLOY.md](DEPLOY.md) — VPS and GitHub Actions deployment.
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) — public-release safety checklist.
- [LICENSE](LICENSE) — MIT license.

## Проверки / Checks

```bash
pytest -q
ruff check .
ruff format --check .
uv lock --check
```
