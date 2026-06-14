from unittest.mock import AsyncMock

from meme_stealer_bot.app import MemeStealerApp, create_dispatcher
from meme_stealer_bot.storage import Storage


def test_dispatcher_can_be_created(tmp_path) -> None:
    dispatcher = create_dispatcher(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)

    assert dispatcher.sub_routers


async def test_start_command_creates_new_screen_without_deleting_user_message(tmp_path) -> None:
    bot = AsyncMock()
    app = MemeStealerApp(bot, Storage(tmp_path / "bot.sqlite3"), 1)
    app.screens = AsyncMock()
    message = AsyncMock()
    message.text = "/start"
    state = AsyncMock()

    await app.start(message, state)

    app.screens.send_main.assert_awaited_once_with()
    message.delete.assert_not_awaited()


async def test_settings_command_creates_new_settings_screen(tmp_path) -> None:
    bot = AsyncMock()
    app = MemeStealerApp(bot, Storage(tmp_path / "bot.sqlite3"), 1)
    app.screens = AsyncMock()
    message = AsyncMock()
    state = AsyncMock()

    await app.settings(message, state)

    app.screens.send_settings.assert_awaited_once_with()


async def test_inline_section_edits_callback_message(tmp_path) -> None:
    bot = AsyncMock()
    app = MemeStealerApp(bot, Storage(tmp_path / "bot.sqlite3"), 1)
    app.screens = AsyncMock()
    callback = AsyncMock()
    callback.data = "screen:status"
    callback.message.message_id = 42
    state = AsyncMock()

    await app.screen_callback(callback, state)

    app.screens.edit_status.assert_awaited_once_with(42)
