from __future__ import annotations

from datetime import UTC, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardRemove

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

    async def send_main(self) -> None:
        await self.remove_reply_keyboard()
        await self.send(MAIN_TEXT, reply_markup=main_keyboard())

    async def send_settings(self) -> None:
        await self.remove_reply_keyboard()
        settings = await self.storage.get_settings(self.user_id)
        await self.send("Настройки публикации:", reply_markup=settings_keyboard(settings))

    async def remove_reply_keyboard(self) -> None:
        settings = await self.storage.get_settings(self.user_id)
        if settings.reply_keyboard_removed:
            return
        message = await self.bot.send_message(
            self.user_id, "Нижнее меню отключено.", reply_markup=ReplyKeyboardRemove()
        )
        await self.storage.mark_reply_keyboard_removed(self.user_id)
        try:
            await self.bot.delete_message(self.user_id, message.message_id)
        except TelegramBadRequest:
            pass

    async def edit_main(self, message_id: int) -> None:
        await self.edit(message_id, MAIN_TEXT, reply_markup=main_keyboard())

    async def edit_settings(self, message_id: int) -> None:
        settings = await self.storage.get_settings(self.user_id)
        await self.edit(
            message_id, "Настройки публикации:", reply_markup=settings_keyboard(settings)
        )

    async def edit_status(self, message_id: int) -> None:
        settings = await self.storage.get_settings(self.user_id)
        text = await build_status_text(self.storage, settings)
        await self.edit(message_id, text, reply_markup=back_keyboard())

    async def edit_help(self, message_id: int) -> None:
        await self.edit(message_id, HELP_TEXT, reply_markup=back_keyboard())

    async def edit_input(self, message_id: int, text: str) -> None:
        await self.edit(message_id, text, reply_markup=back_keyboard())

    async def edit(
        self,
        message_id: int,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        try:
            await self.bot.edit_message_text(
                chat_id=self.user_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
            )
        except TelegramBadRequest as error:
            if "message is not modified" in error.message.lower():
                return
            await self.send(text, reply_markup=reply_markup)

    async def send(
        self,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        await self.bot.send_message(self.user_id, text, reply_markup=reply_markup)
