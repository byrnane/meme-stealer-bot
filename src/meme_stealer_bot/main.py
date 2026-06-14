from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from .app import create_dispatcher
from .config import Config
from .storage import Storage


async def main() -> None:
    config = Config.from_env()
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    storage = Storage(config.database_path)
    await storage.initialize()
    bot = Bot(config.bot_token)
    dispatcher = create_dispatcher(bot, storage, config.owner_id)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
