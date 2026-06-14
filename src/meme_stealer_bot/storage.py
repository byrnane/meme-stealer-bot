from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

from .models import Draft, MediaItem, RichText, UserSettings

PENDING_TEXT_TTL = timedelta(minutes=10)


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    channel_title TEXT,
                    signature_json TEXT,
                    instant_publish INTEGER NOT NULL DEFAULT 0,
                    screen_message_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS pending_text (
                    user_id INTEGER PRIMARY KEY,
                    rich_text_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    media_json TEXT NOT NULL,
                    caption_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            columns = {
                row[1] for row in await (await db.execute("PRAGMA table_info(settings)")).fetchall()
            }
            if "screen_message_id" not in columns:
                await db.execute("ALTER TABLE settings ADD COLUMN screen_message_id INTEGER")
            await db.commit()

    async def get_settings(self, user_id: int) -> UserSettings:
        async with aiosqlite.connect(self.path) as db:
            row = await (
                await db.execute(
                    "SELECT channel_id, channel_title, signature_json, instant_publish, "
                    "screen_message_id "
                    "FROM settings WHERE user_id = ?",
                    (user_id,),
                )
            ).fetchone()
        if not row:
            return UserSettings(user_id=user_id)
        return UserSettings(
            user_id=user_id,
            channel_id=row[0],
            channel_title=row[1],
            signature=RichText.from_dict(json.loads(row[2])) if row[2] else None,
            instant_publish=bool(row[3]),
            screen_message_id=row[4],
        )

    async def _ensure_settings(self, db: aiosqlite.Connection, user_id: int) -> None:
        await db.execute("INSERT OR IGNORE INTO settings(user_id) VALUES (?)", (user_id,))

    async def set_channel(self, user_id: int, channel_id: int, channel_title: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await self._ensure_settings(db, user_id)
            await db.execute(
                "UPDATE settings SET channel_id = ?, channel_title = ? WHERE user_id = ?",
                (channel_id, channel_title, user_id),
            )
            await db.commit()

    async def set_signature(self, user_id: int, signature: RichText | None) -> None:
        value = json.dumps(signature.to_dict(), ensure_ascii=False) if signature else None
        async with aiosqlite.connect(self.path) as db:
            await self._ensure_settings(db, user_id)
            await db.execute(
                "UPDATE settings SET signature_json = ? WHERE user_id = ?", (value, user_id)
            )
            await db.commit()

    async def toggle_publish_mode(self, user_id: int) -> bool:
        settings = await self.get_settings(user_id)
        new_value = not settings.instant_publish
        async with aiosqlite.connect(self.path) as db:
            await self._ensure_settings(db, user_id)
            await db.execute(
                "UPDATE settings SET instant_publish = ? WHERE user_id = ?",
                (int(new_value), user_id),
            )
            await db.commit()
        return new_value

    async def set_screen_message_id(self, user_id: int, message_id: int | None) -> None:
        async with aiosqlite.connect(self.path) as db:
            await self._ensure_settings(db, user_id)
            await db.execute(
                "UPDATE settings SET screen_message_id = ? WHERE user_id = ?",
                (message_id, user_id),
            )
            await db.commit()

    async def set_pending_text(self, user_id: int, text: RichText) -> None:
        expires = datetime.now(UTC) + PENDING_TEXT_TTL
        value = json.dumps(text.to_dict(), ensure_ascii=False)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO pending_text(user_id, rich_text_json, expires_at) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET rich_text_json=excluded.rich_text_json, "
                "expires_at=excluded.expires_at",
                (user_id, value, expires.isoformat()),
            )
            await db.commit()

    async def get_pending_text(self, user_id: int) -> RichText | None:
        async with aiosqlite.connect(self.path) as db:
            row = await (
                await db.execute(
                    "SELECT rich_text_json, expires_at FROM pending_text WHERE user_id = ?",
                    (user_id,),
                )
            ).fetchone()
        if not row:
            return None
        if datetime.fromisoformat(row[1]) <= datetime.now(UTC):
            await self.clear_pending_text(user_id)
            return None
        return RichText.from_dict(json.loads(row[0]))

    async def get_pending_text_details(self, user_id: int) -> tuple[RichText, datetime] | None:
        async with aiosqlite.connect(self.path) as db:
            row = await (
                await db.execute(
                    "SELECT rich_text_json, expires_at FROM pending_text WHERE user_id = ?",
                    (user_id,),
                )
            ).fetchone()
        if not row:
            return None
        expires_at = datetime.fromisoformat(row[1])
        if expires_at <= datetime.now(UTC):
            await self.clear_pending_text(user_id)
            return None
        text = RichText.from_dict(json.loads(row[0]))
        return (text, expires_at) if text else None

    async def pop_pending_text(self, user_id: int) -> RichText | None:
        text = await self.get_pending_text(user_id)
        await self.clear_pending_text(user_id)
        return text

    async def clear_pending_text(self, user_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM pending_text WHERE user_id = ?", (user_id,))
            await db.commit()

    async def create_draft(self, draft: Draft) -> int:
        media_json = json.dumps([item.to_dict() for item in draft.media])
        caption_json = (
            json.dumps(draft.caption.to_dict(), ensure_ascii=False) if draft.caption else None
        )
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO drafts(user_id, media_json, caption_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (draft.user_id, media_json, caption_json, datetime.now(UTC).isoformat()),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def get_draft(self, draft_id: int, user_id: int) -> Draft | None:
        async with aiosqlite.connect(self.path) as db:
            row = await (
                await db.execute(
                    "SELECT media_json, caption_json FROM drafts WHERE id = ? AND user_id = ?",
                    (draft_id, user_id),
                )
            ).fetchone()
        if not row:
            return None
        return Draft(
            id=draft_id,
            user_id=user_id,
            media=[MediaItem.from_dict(item) for item in json.loads(row[0])],
            caption=RichText.from_dict(json.loads(row[1])) if row[1] else None,
        )

    async def delete_draft(self, draft_id: int, user_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM drafts WHERE id = ? AND user_id = ?", (draft_id, user_id))
            await db.commit()

    async def clear_drafts(self, user_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM drafts WHERE user_id = ?", (user_id,))
            await db.commit()

    async def count_drafts(self, user_id: int) -> int:
        async with aiosqlite.connect(self.path) as db:
            row = await (
                await db.execute("SELECT COUNT(*) FROM drafts WHERE user_id = ?", (user_id,))
            ).fetchone()
        return int(row[0])
