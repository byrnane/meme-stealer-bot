from __future__ import annotations

from datetime import UTC, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove

from .keyboards import back_keyboard, main_keyboard, settings_keyboard
from .models import RichText, UserSettings
from .storage import Storage

MAIN_TEXT = (
    "Meme Stealer Bot\n\n"
    "Пришли текст, затем мем. Я очищу репост и подготовлю публикацию.\n"
    "Используй кнопки ниже для управления."
)

HELP_TEXT = (
    "Помощь\n\n"
    "1. Отправь текст комментария, если он нужен.\n"
    "2. Перешли мем или отправь своё медиа.\n"
    "3. Подтверди публикацию в превью.\n\n"
    "Поддерживаются фото, GIF, видео и фото/видео-альбомы.\n"
    "Текст ждёт следующий мем 10 минут."
)


def preview_text(value: RichText | None, limit: int = 80) -> str:
    if not value or not value.text:
        return "не задан"
    compact = " ".join(value.text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


async def build_status_text(storage: Storage, settings: UserSettings) -> str:
    pending = await storage.get_pending_text_details(settings.user_id)
    drafts = await storage.count_drafts(settings.user_id)
    if pending:
        text, expires_at = pending
        seconds = max(0, int((expires_at - datetime.now(UTC)).total_seconds()))
        pending_text = f"{preview_text(text)} (ещё {max(1, (seconds + 59) // 60)} мин.)"
    else:
        pending_text = "нет"
    return (
        "Статус\n\n"
        f"Канал: {settings.channel_title or 'не выбран'}\n"
        f"Публикация: {'мгновенно' if settings.instant_publish else 'с подтверждением'}\n"
        f"Общая подпись: {preview_text(settings.signature)}\n"
        f"Ожидающий комментарий: {pending_text}\n"
        f"Черновики: {drafts}"
    )


class ScreenManager:
    def __init__(self, bot: Bot, storage: Storage, user_id: int) -> None:
        self.bot = bot
        self.storage = storage
        self.user_id = user_id

    async def show_main(self, *, force_new: bool = False) -> None:
        settings = await self.storage.get_settings(self.user_id)
        if force_new or settings.screen_message_id is None:
            await self.replace(MAIN_TEXT, reply_markup=main_keyboard())
            return
        await self.show(MAIN_TEXT)

    async def show_settings(self) -> None:
        settings = await self.storage.get_settings(self.user_id)
        await self.show("Настройки публикации:", reply_markup=settings_keyboard(settings))

    async def show_status(self) -> None:
        settings = await self.storage.get_settings(self.user_id)
        text = await build_status_text(self.storage, settings)
        await self.show(text, reply_markup=back_keyboard())

    async def show_help(self) -> None:
        await self.show(HELP_TEXT, reply_markup=back_keyboard())

    async def begin_input(self, text: str) -> None:
        await self.replace(text, reply_markup=ReplyKeyboardRemove())

    async def show(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
        force_new: bool = False,
    ) -> None:
        settings = await self.storage.get_settings(self.user_id)
        message_id = settings.screen_message_id
        if message_id and not force_new and not isinstance(reply_markup, ReplyKeyboardMarkup):
            try:
                await self.bot.edit_message_text(
                    chat_id=self.user_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=reply_markup,
                )
                return
            except TelegramBadRequest as error:
                if "message is not modified" in error.message.lower():
                    return
        await self.replace(text, reply_markup=reply_markup)

    async def replace(
        self,
        text: str,
        *,
        reply_markup: (
            InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | None
        ) = None,
    ) -> None:
        settings = await self.storage.get_settings(self.user_id)
        old_message_id = settings.screen_message_id
        message = await self.bot.send_message(self.user_id, text, reply_markup=reply_markup)
        await self.storage.set_screen_message_id(self.user_id, message.message_id)
        if old_message_id and old_message_id != message.message_id:
            try:
                await self.bot.delete_message(self.user_id, old_message_id)
            except TelegramBadRequest:
                pass
