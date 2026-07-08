from pathlib import Path

import pytest

from meme_stealer_bot.config import Config, validate_config


def test_validate_config_accepts_required_values() -> None:
    config = validate_config(
        bot_token="token",
        owner_id="123",
        database_path="data/custom.sqlite3",
        log_level="warning",
    )

    assert config == Config(
        bot_token="token",
        owner_id=123,
        database_path=Path("data/custom.sqlite3"),
        log_level="WARNING",
    )


def test_validate_config_reports_all_invalid_values() -> None:
    with pytest.raises(ValueError) as error:
        validate_config(
            bot_token="123456:replace-me",
            owner_id="not-number",
            database_path="",
            log_level="LOUD",
        )

    text = str(error.value)
    assert "BOT_TOKEN is required" in text
    assert "OWNER_ID must be an integer" in text
    assert "DATABASE_PATH is required" in text
    assert "LOG_LEVEL must be one of" in text
