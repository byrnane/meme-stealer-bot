from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat, MenuButtonCommands

logger = logging.getLogger(__name__)

OWNER_COMMANDS = [
    BotCommand(command="start", description="Открыть главное меню"),
    BotCommand(command="settings", description="Настройки публикации"),
    BotCommand(command="cancel", description="Сбросить текущий ввод"),
]


async def configure_owner_menu(bot: Bot, owner_id: int) -> None:
    try:
        await bot.set_my_commands(OWNER_COMMANDS, scope=BotCommandScopeChat(chat_id=owner_id))
        await bot.set_chat_menu_button(chat_id=owner_id, menu_button=MenuButtonCommands())
    except TelegramAPIError as error:
        logger.warning("Could not configure Telegram command menu: %s", error)
