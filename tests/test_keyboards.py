from meme_stealer_bot.keyboards import main_keyboard


def test_main_keyboard_has_inline_sections() -> None:
    keyboard = main_keyboard()

    assert [[button.callback_data for button in row] for row in keyboard.inline_keyboard] == [
        ["screen:settings", "screen:status"],
        ["screen:help"],
    ]
