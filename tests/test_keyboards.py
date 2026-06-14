from meme_stealer_bot.keyboards import (
    CANCEL_BUTTON,
    HELP_BUTTON,
    SETTINGS_BUTTON,
    STATUS_BUTTON,
    main_keyboard,
)


def test_main_keyboard_has_expected_two_by_two_layout() -> None:
    keyboard = main_keyboard()

    assert [[button.text for button in row] for row in keyboard.keyboard] == [
        [SETTINGS_BUTTON, STATUS_BUTTON],
        [CANCEL_BUTTON, HELP_BUTTON],
    ]
    assert keyboard.is_persistent is True
    assert keyboard.resize_keyboard is True
