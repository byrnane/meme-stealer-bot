from unittest.mock import AsyncMock

from meme_stealer_bot.app import create_dispatcher
from meme_stealer_bot.storage import Storage


def test_dispatcher_can_be_created(tmp_path) -> None:
    dispatcher = create_dispatcher(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)

    assert dispatcher.sub_routers


def test_menu_button_text_is_registered_as_handler_before_plain_text(tmp_path) -> None:
    dispatcher = create_dispatcher(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)
    router = dispatcher.sub_routers[0]
    handlers = router.observers["message"].handlers

    callback_names = [handler.callback.__name__ for handler in handlers]
    settings_button_index = callback_names.index("settings", 3)
    plain_text_index = callback_names.index("receive_text")

    assert settings_button_index < plain_text_index
