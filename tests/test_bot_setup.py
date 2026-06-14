from unittest.mock import AsyncMock

from aiogram.types import BotCommandScopeChat, MenuButtonCommands

from meme_stealer_bot.bot_setup import OWNER_COMMANDS, configure_owner_menu


async def test_configure_owner_menu_registers_commands_for_owner_chat() -> None:
    bot = AsyncMock()

    await configure_owner_menu(bot, 123)

    bot.set_my_commands.assert_awaited_once()
    assert bot.set_my_commands.await_args.args == (OWNER_COMMANDS,)
    assert bot.set_my_commands.await_args.kwargs == {"scope": BotCommandScopeChat(chat_id=123)}
    bot.set_chat_menu_button.assert_awaited_once_with(chat_id=123, menu_button=MenuButtonCommands())
