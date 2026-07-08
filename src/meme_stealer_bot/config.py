from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
PLACEHOLDER_BOT_TOKEN = "123456:replace-me"
PLACEHOLDER_OWNER_ID = "123456789"


@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    owner_id: int
    database_path: Path
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        return validate_config(
            bot_token=os.getenv("BOT_TOKEN", ""),
            owner_id=os.getenv("OWNER_ID", ""),
            database_path=os.getenv("DATABASE_PATH", "data/bot.sqlite3"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


def validate_config(
    *,
    bot_token: str,
    owner_id: str,
    database_path: str,
    log_level: str,
) -> Config:
    token = bot_token.strip()
    owner = owner_id.strip()
    path = database_path.strip()
    level = log_level.strip().upper()
    problems: list[str] = []

    if not token or token == PLACEHOLDER_BOT_TOKEN:
        problems.append("BOT_TOKEN is required")
    if not owner or owner == PLACEHOLDER_OWNER_ID:
        problems.append("OWNER_ID is required")
    elif not owner.lstrip("-").isdigit():
        problems.append("OWNER_ID must be an integer")
    if not path:
        problems.append("DATABASE_PATH is required")
    if level not in ALLOWED_LOG_LEVELS:
        allowed = ", ".join(sorted(ALLOWED_LOG_LEVELS))
        problems.append(f"LOG_LEVEL must be one of: {allowed}")

    if problems:
        raise ValueError("; ".join(problems))

    return Config(
        bot_token=token,
        owner_id=int(owner),
        database_path=Path(path),
        log_level=level,
    )
