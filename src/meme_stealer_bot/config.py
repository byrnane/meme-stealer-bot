from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    owner_id: int
    database_path: Path
    log_level: str

    @classmethod
    def from_env(cls) -> Config:
        token = os.getenv("BOT_TOKEN", "").strip()
        owner_id = os.getenv("OWNER_ID", "").strip()
        if not token:
            raise ValueError("BOT_TOKEN is required")
        if not owner_id:
            raise ValueError("OWNER_ID is required")
        return cls(
            bot_token=token,
            owner_id=int(owner_id),
            database_path=Path(os.getenv("DATABASE_PATH", "data/bot.sqlite3")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
