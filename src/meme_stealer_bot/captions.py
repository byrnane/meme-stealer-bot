from __future__ import annotations

from aiogram.types import MessageEntity

from .models import RichText

CAPTION_LIMIT = 1024


def utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def combine_rich_text(first: RichText | None, second: RichText | None) -> RichText | None:
    parts = [part for part in (first, second) if part and part.text]
    if not parts:
        return None
    if len(parts) == 1:
        return RichText(parts[0].text, [entity.model_copy() for entity in parts[0].entities])

    separator = "\n\n"
    offset = utf16_length(parts[0].text + separator)
    entities = [entity.model_copy() for entity in parts[0].entities]
    entities.extend(
        entity.model_copy(update={"offset": entity.offset + offset}) for entity in parts[1].entities
    )
    return RichText(parts[0].text + separator + parts[1].text, entities)


def caption_is_too_long(caption: RichText | None) -> bool:
    return bool(caption and utf16_length(caption.text) > CAPTION_LIMIT)


def plain_rich_text(text: str, entities: list[MessageEntity] | None = None) -> RichText:
    return RichText(text=text, entities=list(entities or []))
