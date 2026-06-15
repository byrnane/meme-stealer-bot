from __future__ import annotations

from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)

from .models import Draft, MediaItem, RichText


def draft_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Опубликовать", callback_data=f"draft:publish:{draft_id}"
                ),
                InlineKeyboardButton(text="Отменить", callback_data=f"draft:cancel:{draft_id}"),
            ]
        ]
    )


class Publisher:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @staticmethod
    def _caption_args(caption: RichText | None) -> dict:
        return {
            "caption": caption.text if caption else None,
            "caption_entities": caption.entities if caption else None,
        }

    async def send(
        self,
        chat_id: int,
        draft: Draft,
        *,
        preview_draft_id: int | None = None,
        disable_notification: bool = False,
    ) -> None:
        reply_markup = draft_keyboard(preview_draft_id) if preview_draft_id is not None else None
        if len(draft.media) > 1:
            media = []
            for index, item in enumerate(draft.media):
                caption = draft.caption if index == 0 else None
                if item.kind == "photo":
                    media.append(
                        InputMediaPhoto(
                            media=item.file_id,
                            has_spoiler=item.has_spoiler,
                            **self._caption_args(caption),
                        )
                    )
                elif item.kind == "video":
                    media.append(
                        InputMediaVideo(
                            media=item.file_id,
                            has_spoiler=item.has_spoiler,
                            **self._caption_args(caption),
                        )
                    )
            await self.bot.send_media_group(
                chat_id=chat_id,
                media=media,
                disable_notification=disable_notification,
            )
            if reply_markup:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="Опубликовать этот альбом?",
                    reply_markup=reply_markup,
                    disable_notification=disable_notification,
                )
            return

        item = draft.media[0]
        common = {
            **self._caption_args(draft.caption),
            "reply_markup": reply_markup,
            "disable_notification": disable_notification,
        }
        if item.kind == "photo":
            await self.bot.send_photo(
                chat_id=chat_id, photo=item.file_id, has_spoiler=item.has_spoiler, **common
            )
        elif item.kind == "video":
            await self.bot.send_video(
                chat_id=chat_id,
                video=item.file_id,
                has_spoiler=item.has_spoiler,
                supports_streaming=True,
                **common,
            )
        else:
            await self.bot.send_animation(
                chat_id=chat_id,
                animation=item.file_id,
                has_spoiler=item.has_spoiler,
                **common,
            )


def media_item_from_message(message) -> MediaItem | None:
    if message.photo:
        return MediaItem("photo", message.photo[-1].file_id, bool(message.has_media_spoiler))
    if message.video:
        return MediaItem("video", message.video.file_id, bool(message.has_media_spoiler))
    if message.animation:
        return MediaItem("animation", message.animation.file_id, bool(message.has_media_spoiler))
    return None
