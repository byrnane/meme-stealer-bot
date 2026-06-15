from unittest.mock import AsyncMock

from meme_stealer_bot.models import Draft, MediaItem, RichText
from meme_stealer_bot.publishing import Publisher


async def test_publisher_sends_clean_file_id_and_caption() -> None:
    bot = AsyncMock()
    draft = Draft(None, 1, [MediaItem("photo", "telegram-file-id")], RichText("текст", []))

    await Publisher(bot).send(-100123, draft)

    bot.send_photo.assert_awaited_once_with(
        chat_id=-100123,
        photo="telegram-file-id",
        has_spoiler=False,
        caption="текст",
        caption_entities=[],
        reply_markup=None,
        disable_notification=False,
    )


async def test_publisher_sends_mixed_album_with_caption_only_on_first_item() -> None:
    bot = AsyncMock()
    draft = Draft(
        None,
        1,
        [MediaItem("photo", "photo-id"), MediaItem("video", "video-id")],
        RichText("текст", []),
    )

    await Publisher(bot).send(-100123, draft)

    media = bot.send_media_group.await_args.kwargs["media"]
    assert len(media) == 2
    assert media[0].caption == "текст"
    assert media[1].caption is None
    assert bot.send_media_group.await_args.kwargs["disable_notification"] is False


async def test_publisher_can_send_silently() -> None:
    bot = AsyncMock()
    draft = Draft(None, 1, [MediaItem("photo", "telegram-file-id")], RichText("текст", []))

    await Publisher(bot).send(-100123, draft, disable_notification=True)

    bot.send_photo.assert_awaited_once_with(
        chat_id=-100123,
        photo="telegram-file-id",
        has_spoiler=False,
        caption="текст",
        caption_entities=[],
        reply_markup=None,
        disable_notification=True,
    )
