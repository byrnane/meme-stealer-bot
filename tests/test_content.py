from types import SimpleNamespace

from meme_stealer_bot.app import personal_caption_from_messages
from meme_stealer_bot.models import RichText


def message(*, caption=None, caption_entities=None, forward_origin=None):
    return SimpleNamespace(
        caption=caption,
        caption_entities=caption_entities or [],
        forward_origin=forward_origin,
    )


def test_forwarded_caption_is_removed_and_pending_comment_is_used() -> None:
    pending = RichText("мой комментарий", [])
    forwarded = message(caption="реклама и ссылка оригинала", forward_origin=object())

    assert personal_caption_from_messages([forwarded], pending) == pending


def test_direct_media_caption_wins_over_pending_comment() -> None:
    pending = RichText("старый текст", [])

    result = personal_caption_from_messages([message(caption="моя подпись")], pending)

    assert result == RichText("моя подпись", [])
