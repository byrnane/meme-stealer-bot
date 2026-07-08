from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from .config import validate_config
from .main import main
from .storage import Storage


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/bot.sqlite3"))


async def initialize_database() -> None:
    path = database_path()
    await Storage(path).initialize()
    print(f"База данных готова: {path.resolve()}")


def doctor() -> int:
    path_value = os.getenv("DATABASE_PATH", "data/bot.sqlite3")
    path = Path(path_value)
    problems: list[str] = []
    try:
        validate_config(
            bot_token=os.getenv("BOT_TOKEN", ""),
            owner_id=os.getenv("OWNER_ID", ""),
            database_path=path_value,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    except ValueError as error:
        problems.extend(str(error).split("; "))

    print(f".env: {'найден' if Path('.env').exists() else 'не найден'}")
    database_status = "найдена" if path.exists() else "будет создана при запуске"
    print(f"База данных: {path.resolve()} ({database_status})")
    if problems:
        for problem in problems:
            print(f"Проблема: {problem}")
        return 1
    print("Обязательные настройки заполнены. Можно запускать бота.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Meme Stealer Bot")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("start", "init-db", "doctor"),
        default="start",
        help="start запускает бота, init-db создаёт базу, doctor проверяет настройки",
    )
    return parser


def run() -> None:
    load_dotenv()
    command = build_parser().parse_args().command
    if command == "init-db":
        asyncio.run(initialize_database())
        return
    if command == "doctor":
        raise SystemExit(doctor())
    asyncio.run(main())
