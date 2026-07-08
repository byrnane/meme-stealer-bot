from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage

from meme_stealer_bot.app import MemeStealerApp, create_dispatcher
from meme_stealer_bot.models import Draft, MediaItem, RichText
from meme_stealer_bot.storage import Storage


def media_message(**overrides):
    values = {
        "photo": [SimpleNamespace(file_id="photo-id")],
        "video": None,
        "animation": None,
        "has_media_spoiler": False,
        "caption": None,
        "caption_entities": [],
        "forward_origin": None,
        "media_group_id": None,
        "answer": AsyncMock(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


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


async def test_text_media_preview_publish_flow_clears_state(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_channel(1, -1001, "Мемы")
    bot = AsyncMock()
    app = MemeStealerApp(bot, storage, 1)
    app.publisher = AsyncMock()

    text_message = AsyncMock()
    text_message.text = "мой текст"
    text_message.entities = []
    await app.receive_text(text_message)
    media = media_message()
    await app.process_media_messages([media])

    assert await storage.get_pending_text(1) is None
    assert await storage.count_drafts(1) == 1
    draft_id = app.publisher.send.await_args_list[0].args[1].id
    callback = AsyncMock()
    callback.data = f"draft:publish:{draft_id}"

    await app.draft_callback(callback)

    assert await storage.count_drafts(1) == 0
    assert app.publisher.send.await_count == 2
    publish_call = app.publisher.send.await_args_list[1]
    assert publish_call.args[0] == -1001
    assert publish_call.kwargs == {"disable_notification": True}


async def test_publish_error_releases_draft_for_retry(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_channel(1, -1001, "Мемы")
    draft_id = await storage.create_draft(
        Draft(None, 1, [MediaItem("photo", "photo-id")], RichText("текст", []))
    )
    bot = AsyncMock()
    app = MemeStealerApp(bot, storage, 1)
    app.publisher = AsyncMock()
    app.publisher.send.side_effect = TelegramBadRequest(
        method=SendMessage(chat_id=-1001, text="x"),
        message="publish failed",
    )
    callback = AsyncMock()
    callback.data = f"draft:publish:{draft_id}"

    await app.draft_callback(callback)

    assert await storage.get_draft(draft_id, 1) is not None
    callback.answer.assert_awaited_once_with(
        "Не удалось опубликовать. Проверь права бота.", show_alert=True
    )


async def test_double_publish_callback_sends_once(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_channel(1, -1001, "Мемы")
    draft_id = await storage.create_draft(
        Draft(None, 1, [MediaItem("photo", "photo-id")], RichText("текст", []))
    )
    bot = AsyncMock()
    app = MemeStealerApp(bot, storage, 1)
    app.publisher = AsyncMock()
    first = AsyncMock()
    first.data = f"draft:publish:{draft_id}"
    second = AsyncMock()
    second.data = f"draft:publish:{draft_id}"

    await app.draft_callback(first)
    await app.draft_callback(second)

    app.publisher.send.assert_awaited_once()
    second.answer.assert_awaited_once_with("Черновик уже обработан.", show_alert=True)


async def test_bad_callback_data_does_not_crash(tmp_path) -> None:
    app = MemeStealerApp(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)
    state = AsyncMock()

    draft = AsyncMock()
    draft.data = "draft:publish:not-a-number"
    await app.draft_callback(draft)

    screen = AsyncMock()
    screen.data = "screen:unknown"
    screen.message.message_id = 42
    await app.screen_callback(screen, state)

    settings = AsyncMock()
    settings.data = "settings:unknown"
    settings.message = None
    await app.settings_callback(settings, state)

    draft.answer.assert_awaited_once_with("Кнопка устарела. Открой меню заново.", show_alert=True)
    screen.answer.assert_awaited_once_with("Кнопка устарела. Открой меню заново.", show_alert=True)
    settings.answer.assert_awaited_once_with(
        "Кнопка устарела. Открой меню заново.", show_alert=True
    )


async def test_unauthorized_user_gets_private_bot_response(tmp_path) -> None:
    app = MemeStealerApp(AsyncMock(), Storage(tmp_path / "bot.sqlite3"), 1)
    message = AsyncMock()
    callback = AsyncMock()

    await app.unauthorized(message)
    await app.unauthorized_callback(callback)

    message.answer.assert_awaited_once_with("Этот бот личный.")
    callback.answer.assert_awaited_once_with("Этот бот личный.", show_alert=True)
