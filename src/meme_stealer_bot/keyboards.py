from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from .models import UserSettings

SETTINGS_BUTTON = "⚙️ Настройки"
STATUS_BUTTON = "📊 Статус"
CANCEL_BUTTON = "🧹 Отмена"
HELP_BUTTON = "ℹ️ Помощь"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SETTINGS_BUTTON), KeyboardButton(text=STATUS_BUTTON)],
            [KeyboardButton(text=CANCEL_BUTTON), KeyboardButton(text=HELP_BUTTON)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Пришли текст или мем",
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Главное меню", callback_data="screen:main")]]
    )


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
            [InlineKeyboardButton(text="← Главное меню", callback_data="screen:main")],
        ]
    )
