from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText
from aiogram.types import ReplyKeyboardRemove

from meme_stealer_bot.models import Draft, MediaItem, RichText
from meme_stealer_bot.screens import ScreenManager, build_status_text
from meme_stealer_bot.storage import Storage


async def test_screen_manager_edits_saved_screen(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_screen_message_id(1, 42)
    bot = AsyncMock()
    screens = ScreenManager(bot, storage, 1)

    await screens.show_help()

    bot.edit_message_text.assert_awaited_once()
    bot.send_message.assert_not_awaited()


async def test_screen_manager_recreates_deleted_screen(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_screen_message_id(1, 42)
    bot = AsyncMock()
    bot.edit_message_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=1, message_id=42, text="x"),
        message="message to edit not found",
    )
    bot.send_message.return_value = SimpleNamespace(message_id=43)
    screens = ScreenManager(bot, storage, 1)

    await screens.show_help()

    assert (await storage.get_settings(1)).screen_message_id == 43
    bot.delete_message.assert_awaited_once_with(1, 42)


async def test_screen_manager_keeps_screen_when_content_is_unchanged(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_screen_message_id(1, 42)
    bot = AsyncMock()
    bot.edit_message_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=1, message_id=42, text="x"),
        message="message is not modified",
    )
    screens = ScreenManager(bot, storage, 1)

    await screens.show_help()

    bot.send_message.assert_not_awaited()
    assert (await storage.get_settings(1)).screen_message_id == 42


async def test_begin_input_replaces_screen_and_hides_reply_keyboard(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_screen_message_id(1, 42)
    bot = AsyncMock()
    bot.send_message.return_value = SimpleNamespace(message_id=43)
    screens = ScreenManager(bot, storage, 1)

    await screens.begin_input("Введи значение")

    reply_markup = bot.send_message.await_args.kwargs["reply_markup"]
    assert isinstance(reply_markup, ReplyKeyboardRemove)
    assert (await storage.get_settings(1)).screen_message_id == 43


async def test_full_status_contains_settings_pending_text_and_drafts(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_channel(1, -1001, "Мемы")
    await storage.set_signature(1, RichText("Общая подпись", []))
    await storage.set_pending_text(1, RichText("Комментарий", []))
    await storage.create_draft(Draft(None, 1, [MediaItem("photo", "id")], None))

    text = await build_status_text(storage, await storage.get_settings(1))

    assert "Канал: Мемы" in text
    assert "Общая подпись: Общая подпись" in text
    assert "Ожидающий комментарий: Комментарий" in text
    assert "Черновики: 1" in text
