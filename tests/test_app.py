from unittest.mock import AsyncMock

from meme_stealer_bot.app import create_dispatcher
from meme_stealer_bot.storage import Storage


def test_dispatcher_can_be_created(tmp_path) -> None:
    dispatcher = create_dispatcher(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)

    assert dispatcher.sub_routers
