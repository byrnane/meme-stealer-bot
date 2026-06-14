from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from meme_stealer_bot.models import Draft, MediaItem, RichText
from meme_stealer_bot.screens import ScreenManager, build_status_text
from meme_stealer_bot.storage import Storage


async def test_direct_command_sends_new_screen(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.mark_reply_keyboard_removed(1)
    bot = AsyncMock()
    screens = ScreenManager(bot, storage, 1)

    await screens.send_main()

    bot.send_message.assert_awaited_once()
    bot.edit_message_text.assert_not_awaited()


async def test_old_reply_keyboard_is_removed_once(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    bot = AsyncMock()
    bot.send_message.return_value.message_id = 7
    screens = ScreenManager(bot, storage, 1)

    await screens.remove_reply_keyboard()
    await screens.remove_reply_keyboard()

    bot.send_message.assert_awaited_once()
    bot.delete_message.assert_awaited_once_with(1, 7)


async def test_inline_navigation_edits_selected_screen(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    bot = AsyncMock()
    screens = ScreenManager(bot, storage, 1)

    await screens.edit_help(42)

    assert bot.edit_message_text.await_args.kwargs["message_id"] == 42
    bot.send_message.assert_not_awaited()


async def test_missing_inline_screen_falls_back_to_new_message(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    bot = AsyncMock()
    bot.edit_message_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=1, message_id=42, text="x"),
        message="message to edit not found",
    )
    screens = ScreenManager(bot, storage, 1)

    await screens.edit_help(42)

    bot.send_message.assert_awaited_once()
    bot.delete_message.assert_not_awaited()


async def test_unchanged_inline_screen_does_not_send_new_message(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    bot = AsyncMock()
    bot.edit_message_text.side_effect = TelegramBadRequest(
        method=EditMessageText(chat_id=1, message_id=42, text="x"),
        message="message is not modified",
    )
    screens = ScreenManager(bot, storage, 1)

    await screens.edit_help(42)

    bot.send_message.assert_not_awaited()


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
