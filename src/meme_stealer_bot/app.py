from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, MessageOriginChannel

from .captions import caption_is_too_long, combine_rich_text, plain_rich_text
from .collector import AlbumCollector
from .keyboards import HELP_BUTTON, MAIN_BUTTON, SETTINGS_BUTTON, STATUS_BUTTON
from .models import Draft, RichText
from .publishing import Publisher, media_item_from_message
from .screens import ScreenManager
from .states import SettingsState
from .storage import Storage

logger = logging.getLogger(__name__)


def personal_caption_from_messages(
    messages: Sequence[Message], pending: RichText | None
) -> RichText | None:
    if any(message.forward_origin is not None for message in messages):
        return pending
    caption_message = next((message for message in messages if message.caption), None)
    if caption_message:
        return plain_rich_text(caption_message.caption or "", caption_message.caption_entities)
    return pending


class MemeStealerApp:
    def __init__(self, bot: Bot, storage: Storage, owner_id: int) -> None:
        self.bot = bot
        self.storage = storage
        self.owner_id = owner_id
        self.publisher = Publisher(bot)
        self.screens = ScreenManager(bot, storage, owner_id)
        self.router = Router(name="meme-stealer")
        self.album_collector = AlbumCollector(self.process_media_messages)
        self._pending_expiry_task: asyncio.Task | None = None
        self._register_handlers()

    def _owner(self):
        return F.from_user.id == self.owner_id

    def _register_handlers(self) -> None:
        owner = self._owner()
        self.router.message.register(self.start, owner, CommandStart())
        self.router.message.register(self.cancel, owner, Command("cancel"))
        self.router.message.register(self.settings, owner, Command("settings"))
        self.router.message.register(self.status, owner, Command("status"))
        self.router.message.register(self.help, owner, Command("help"))
        self.router.message.register(self.menu, owner, Command("menu"))
        self.router.message.register(self.settings, owner, F.text == SETTINGS_BUTTON)
        self.router.message.register(self.status, owner, F.text == STATUS_BUTTON)
        self.router.message.register(self.menu, owner, F.text == MAIN_BUTTON)
        self.router.message.register(self.help, owner, F.text == HELP_BUTTON)
        self.router.callback_query.register(
            self.screen_callback, owner, F.data.startswith("screen:")
        )
        self.router.callback_query.register(
            self.settings_callback, owner, F.data.startswith("settings:")
        )
        self.router.callback_query.register(self.draft_callback, owner, F.data.startswith("draft:"))
        self.router.message.register(self.receive_channel, owner, SettingsState.waiting_for_channel)
        self.router.message.register(
            self.receive_signature, owner, SettingsState.waiting_for_signature, F.text
        )
        self.router.message.register(
            self.receive_media,
            owner,
            F.content_type.in_({"photo", "video", "animation"}),
        )
        self.router.message.register(self.receive_text, owner, F.text)
        self.router.message.register(self.unsupported, owner)
        self.router.message.register(self.unauthorized)
        self.router.callback_query.register(self.unauthorized_callback)

    async def start(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        await self.screens.show_main(new=True)

    async def menu(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        is_command = self._is_command(message)
        await self.screens.show_main(new=is_command)

    async def cancel(self, message: Message, state: FSMContext) -> None:
        self._cancel_pending_expiry()
        await state.clear()
        await self.storage.clear_pending_text(self.owner_id)
        await self.screens.show_main(new=True)

    async def settings(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        is_command = self._is_command(message)
        await self.screens.show_settings(new=is_command)

    async def status(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        is_command = self._is_command(message)
        await self.screens.show_status(new=is_command)

    async def help(self, message: Message, state: FSMContext) -> None:
        await state.clear()
        is_command = self._is_command(message)
        await self.screens.show_help(new=is_command)

    async def screen_callback(self, callback: CallbackQuery, state: FSMContext) -> None:
        if callback.data == "screen:main":
            await state.clear()
            await self.screens.show_main()
        await callback.answer()

    async def settings_callback(self, callback: CallbackQuery, state: FSMContext) -> None:
        action = callback.data or ""
        if action == "settings:channel":
            await state.set_state(SettingsState.waiting_for_channel)
            await self.screens.begin_input(
                "Перешли любой пост из целевого канала или отправь его @username / числовой ID."
            )
        elif action == "settings:signature":
            await state.set_state(SettingsState.waiting_for_signature)
            await self.screens.begin_input(
                "Отправь новую общую подпись одним текстовым сообщением."
            )
        elif action == "settings:signature:clear":
            await self.storage.set_signature(self.owner_id, None)
            await callback.answer("Общая подпись очищена.")
        elif action == "settings:mode":
            instant = await self.storage.toggle_publish_mode(self.owner_id)
            text = "Теперь публикую мгновенно." if instant else "Теперь показываю превью."
            await callback.answer(text)
        if action in {"settings:channel", "settings:signature"}:
            await callback.answer()
        else:
            await self.screens.show_settings()

    async def receive_channel(self, message: Message, state: FSMContext) -> None:
        channel_ref: int | str | None = None
        if isinstance(message.forward_origin, MessageOriginChannel):
            channel_ref = message.forward_origin.chat.id
        elif message.text:
            value = message.text.strip()
            try:
                channel_ref = int(value)
            except ValueError:
                channel_ref = value if value.startswith("@") else f"@{value}"
        if channel_ref is None:
            await self.screens.begin_input(
                "Не вижу канал.\n\nПерешли пост из него или отправь @username / числовой ID."
            )
            return
        try:
            chat = await self.bot.get_chat(channel_ref)
            if chat.type != ChatType.CHANNEL:
                await self.screens.begin_input(
                    "Это не канал.\n\n"
                    "Перешли пост из канала или отправь его @username / числовой ID."
                )
                return
            me = await self.bot.get_me()
            membership = await self.bot.get_chat_member(chat.id, me.id)
            allowed = membership.status == ChatMemberStatus.CREATOR or (
                membership.status == ChatMemberStatus.ADMINISTRATOR
                and bool(getattr(membership, "can_post_messages", False))
            )
            if not allowed:
                await self.screens.begin_input(
                    "У бота нет права публикации.\n\n"
                    "Добавь его администратором канала с правом публикации и попробуй снова."
                )
                return
        except (TelegramBadRequest, TelegramForbiddenError):
            await self.screens.begin_input(
                "Не удалось открыть канал.\n\nПроверь адрес и права бота, затем попробуй снова."
            )
            return
        await self.storage.set_channel(self.owner_id, chat.id, chat.title or str(chat.id))
        await state.clear()
        await self.screens.show_settings()

    async def receive_signature(self, message: Message, state: FSMContext) -> None:
        signature = plain_rich_text(message.text or "", message.entities)
        if caption_is_too_long(signature):
            await self.screens.begin_input(
                "Подпись длиннее 1024 символов.\n\nСократи её и отправь ещё раз."
            )
            return
        await self.storage.set_signature(self.owner_id, signature)
        await state.clear()
        await self.screens.show_settings()

    async def receive_text(self, message: Message) -> None:
        text = plain_rich_text(message.text or "", message.entities)
        await self.storage.set_pending_text(self.owner_id, text)
        self._cancel_pending_expiry()
        self._pending_expiry_task = asyncio.create_task(self._expire_pending_text())
        await message.answer("Текст сохранён для следующего мема на 10 минут.")

    async def receive_media(self, message: Message) -> None:
        if message.media_group_id:
            await self.album_collector.add(message)
        else:
            await self.process_media_messages([message])

    async def process_media_messages(self, messages: Sequence[Message]) -> None:
        first = messages[0]
        media = [item for message in messages if (item := media_item_from_message(message))]
        if not media:
            await first.answer("В этом сообщении нет поддерживаемого медиа.")
            return
        if len(media) > 1 and any(item.kind == "animation" for item in media):
            await first.answer("GIF нельзя включить в Telegram-альбом.")
            return

        pending = await self.storage.get_pending_text(self.owner_id)
        personal = personal_caption_from_messages(messages, pending)
        settings = await self.storage.get_settings(self.owner_id)
        caption = combine_rich_text(personal, settings.signature)
        if caption_is_too_long(caption):
            await first.answer(
                "Итоговая подпись длиннее 1024 символов. Сократи текст или общую подпись."
            )
            return
        if settings.channel_id is None:
            await first.answer("Сначала выбери канал через /settings.")
            return

        draft = Draft(id=None, user_id=self.owner_id, media=media, caption=caption)
        if settings.instant_publish:
            try:
                await self.publisher.send(settings.channel_id, draft)
                self._cancel_pending_expiry()
                await self.storage.clear_pending_text(self.owner_id)
                await first.answer("Опубликовано.")
            except (TelegramBadRequest, TelegramForbiddenError) as error:
                logger.warning("Publishing failed: %s", error)
                await first.answer("Не удалось опубликовать. Проверь канал и права бота.")
            return

        draft_id = await self.storage.create_draft(draft)
        draft.id = draft_id
        try:
            await self.publisher.send(self.owner_id, draft, preview_draft_id=draft_id)
        except (TelegramBadRequest, TelegramForbiddenError):
            await self.storage.delete_draft(draft_id, self.owner_id)
            await first.answer("Не удалось показать превью. Попробуй отправить мем ещё раз.")
            return
        self._cancel_pending_expiry()
        await self.storage.clear_pending_text(self.owner_id)

    async def draft_callback(self, callback: CallbackQuery) -> None:
        _, action, raw_id = (callback.data or "").split(":")
        draft_id = int(raw_id)
        draft = await self.storage.get_draft(draft_id, self.owner_id)
        if not draft:
            await callback.answer("Черновик уже обработан.", show_alert=True)
            return
        if action == "cancel":
            await self.storage.delete_draft(draft_id, self.owner_id)
            await callback.answer("Черновик отменён.")
            await self._remove_buttons(callback)
            return
        settings = await self.storage.get_settings(self.owner_id)
        if settings.channel_id is None:
            await callback.answer("Сначала выбери канал в /settings.", show_alert=True)
            return
        try:
            await self.publisher.send(settings.channel_id, draft)
        except (TelegramBadRequest, TelegramForbiddenError):
            await callback.answer("Не удалось опубликовать. Проверь права бота.", show_alert=True)
            return
        await self.storage.delete_draft(draft_id, self.owner_id)
        await callback.answer("Опубликовано.")
        await self._remove_buttons(callback)

    async def _remove_buttons(self, callback: CallbackQuery) -> None:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass

    @staticmethod
    def _is_command(message: Message) -> bool:
        return bool(message.text and message.text.startswith("/"))

    async def unsupported(self, message: Message) -> None:
        await message.answer("Поддерживаются только фото, GIF, видео и фото/видео-альбомы.")

    async def unauthorized(self, message: Message) -> None:
        await message.answer("Этот бот личный.")

    async def unauthorized_callback(self, callback: CallbackQuery) -> None:
        await callback.answer("Этот бот личный.", show_alert=True)

    def _cancel_pending_expiry(self) -> None:
        if self._pending_expiry_task:
            self._pending_expiry_task.cancel()
            self._pending_expiry_task = None

    async def _expire_pending_text(self) -> None:
        try:
            await asyncio.sleep(600)
            expired = await self.storage.pop_pending_text(self.owner_id)
            if expired:
                await self.bot.send_message(
                    self.owner_id, "Прошло 10 минут, сохранённый текст сброшен."
                )
        except asyncio.CancelledError:
            return
        finally:
            if self._pending_expiry_task is asyncio.current_task():
                self._pending_expiry_task = None


def create_dispatcher(bot: Bot, storage: Storage, owner_id: int) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(MemeStealerApp(bot, storage, owner_id).router)
    return dispatcher
