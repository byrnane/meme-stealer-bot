from aiogram.enums import MessageEntityType
from aiogram.types import MessageEntity

from meme_stealer_bot.captions import caption_is_too_long, combine_rich_text, utf16_length
from meme_stealer_bot.models import RichText


def test_combines_text_and_shifts_entities_by_utf16_units() -> None:
    first = RichText("мем 😀", [MessageEntity(type=MessageEntityType.BOLD, offset=0, length=3)])
    second = RichText(
        "подпись",
        [MessageEntity(type=MessageEntityType.ITALIC, offset=0, length=7)],
    )

    result = combine_rich_text(first, second)

    assert result is not None
    assert result.text == "мем 😀\n\nподпись"
    assert result.entities[1].offset == utf16_length("мем 😀\n\n")


def test_caption_limit_uses_telegram_utf16_length() -> None:
    assert not caption_is_too_long(RichText("a" * 1024, []))
    assert caption_is_too_long(RichText("😀" * 513, []))
