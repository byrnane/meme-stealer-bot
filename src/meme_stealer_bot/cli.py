from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from .main import main
from .storage import Storage


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/bot.sqlite3"))


async def initialize_database() -> None:
    path = database_path()
    await Storage(path).initialize()
    print(f"База данных готова: {path.resolve()}")


def doctor() -> int:
    token = os.getenv("BOT_TOKEN", "").strip()
    owner_id = os.getenv("OWNER_ID", "").strip()
    path = database_path()
    problems = []

    if not token or token == "123456:replace-me":
        problems.append("BOT_TOKEN не заполнен")
    if not owner_id or owner_id == "123456789":
        problems.append("OWNER_ID не заполнен")
    elif not owner_id.lstrip("-").isdigit():
        problems.append("OWNER_ID должен быть числом")

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
