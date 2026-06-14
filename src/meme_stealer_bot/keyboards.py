from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .models import UserSettings


def settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    channel = settings.channel_title or "не выбран"
    signature = "задана" if settings.signature else "не задана"
    mode = "мгновенно" if settings.instant_publish else "с подтверждением"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Канал: {channel}", callback_data="settings:channel")],
            [
                InlineKeyboardButton(
                    text=f"Общая подпись: {signature}", callback_data="settings:signature"
                ),
                InlineKeyboardButton(text="Очистить", callback_data="settings:signature:clear"),
            ],
            [InlineKeyboardButton(text=f"Публикация: {mode}", callback_data="settings:mode")],
        ]
    )
