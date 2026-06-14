from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from aiogram.types import MessageEntity

MediaKind = Literal["photo", "video", "animation"]


@dataclass(slots=True)
class RichText:
    text: str
    entities: list[MessageEntity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "entities": [
                entity.model_dump(mode="json", exclude_none=True) for entity in self.entities
            ],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> RichText | None:
        if value is None:
            return None
        return cls(
            text=value["text"],
            entities=[MessageEntity.model_validate(entity) for entity in value.get("entities", [])],
        )


@dataclass(slots=True)
class MediaItem:
    kind: MediaKind
    file_id: str
    has_spoiler: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> MediaItem:
        return cls(**value)


@dataclass(slots=True)
class Draft:
    id: int | None
    user_id: int
    media: list[MediaItem]
    caption: RichText | None


@dataclass(slots=True)
class UserSettings:
    user_id: int
    channel_id: int | None = None
    channel_title: str | None = None
    signature: RichText | None = None
    instant_publish: bool = False
    reply_keyboard_removed: bool = False
