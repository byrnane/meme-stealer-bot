from datetime import UTC, datetime, timedelta

import aiosqlite

from meme_stealer_bot.models import Draft, MediaItem, RichText
from meme_stealer_bot.storage import Storage


async def test_pending_text_is_replaced_and_popped(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("первый", []))
    await storage.set_pending_text(1, RichText("второй", []))

    assert await storage.pop_pending_text(1) == RichText("второй", [])
    assert await storage.pop_pending_text(1) is None


async def test_pending_text_can_be_read_without_removing_it(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("комментарий", []))

    assert await storage.get_pending_text(1) == RichText("комментарий", [])
    assert await storage.get_pending_text(1) == RichText("комментарий", [])


async def test_expired_pending_text_is_discarded(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("старый", []))
    expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    async with aiosqlite.connect(storage.path) as db:
        await db.execute("UPDATE pending_text SET expires_at = ?", (expired,))
        await db.commit()

    assert await storage.pop_pending_text(1) is None


async def test_cleanup_expired_pending_text_removes_only_expired_rows(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("старый", []))
    await storage.set_pending_text(2, RichText("свежий", []))
    now = datetime.now(UTC)
    expired = (now - timedelta(seconds=1)).isoformat()
    fresh = (now + timedelta(minutes=10)).isoformat()
    async with aiosqlite.connect(storage.path) as db:
        await db.execute(
            "UPDATE pending_text SET expires_at = CASE user_id WHEN 1 THEN ? ELSE ? END",
            (expired, fresh),
        )
        await db.commit()

    removed = await storage.cleanup_expired_pending_text(now)

    assert removed == 1
    assert await storage.get_pending_text(1) is None
    assert await storage.get_pending_text(2) == RichText("свежий", [])


async def test_pending_details_and_draft_count(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("текст", []))

    details = await storage.get_pending_text_details(1)

    assert details is not None
    assert details[0] == RichText("текст", [])
    assert details[1] > datetime.now(UTC)
    assert await storage.count_drafts(1) == 0


async def test_cleanup_old_drafts_removes_stale_claimed_and_unclaimed_rows(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    old_open = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "old-open")], None))
    old_claimed = await storage.create_draft(
        Draft(None, 1, [MediaItem("photo", "old-claimed")], None)
    )
    fresh = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "fresh")], None))
    assert await storage.claim_draft(old_claimed, 1) is not None
    now = datetime.now(UTC)
    old_created_at = (now - timedelta(days=8)).isoformat()
    async with aiosqlite.connect(storage.path) as db:
        await db.execute(
            "UPDATE drafts SET created_at = ? WHERE id IN (?, ?)",
            (old_created_at, old_open, old_claimed),
        )
        await db.commit()

    removed = await storage.cleanup_old_drafts(now=now)

    assert removed == 2
    assert await storage.get_draft(old_open, 1) is None
    assert await storage.claim_draft(old_claimed, 1) is None
    assert await storage.get_draft(fresh, 1) is not None


async def test_run_maintenance_cleans_expired_pending_text_and_old_drafts(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("старый", []))
    old_draft = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "old")], None))
    fresh_draft = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "fresh")], None))
    expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    old_created_at = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    async with aiosqlite.connect(storage.path) as db:
        await db.execute("UPDATE pending_text SET expires_at = ?", (expired,))
        await db.execute(
            "UPDATE drafts SET created_at = ? WHERE id = ?",
            (old_created_at, old_draft),
        )
        await db.commit()

    await storage.run_maintenance()

    assert await storage.get_pending_text(1) is None
    assert await storage.get_draft(old_draft, 1) is None
    assert await storage.get_draft(fresh_draft, 1) is not None


async def test_reply_keyboard_removal_is_persisted(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()

    await storage.mark_reply_keyboard_removed(1)

    assert (await storage.get_settings(1)).reply_keyboard_removed is True


async def test_draft_can_be_claimed_once_and_released(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    draft_id = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "id")], None))

    claimed = await storage.claim_draft(draft_id, 1)

    assert claimed is not None
    assert claimed.id == draft_id
    assert await storage.claim_draft(draft_id, 1) is None
    assert await storage.get_draft(draft_id, 1) is None
    assert await storage.count_drafts(1) == 0

    await storage.release_draft(draft_id, 1)

    assert await storage.get_draft(draft_id, 1) is not None
    assert await storage.count_drafts(1) == 1


async def test_claimed_draft_is_not_deleted_by_cancel(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    draft_id = await storage.create_draft(Draft(None, 1, [MediaItem("photo", "id")], None))
    assert await storage.claim_draft(draft_id, 1) is not None

    await storage.delete_draft(draft_id, 1)

    assert await storage.claim_draft(draft_id, 1) is None

    await storage.finish_draft(draft_id, 1)

    assert await storage.count_drafts(1) == 0


async def test_initialize_adds_claimed_at_to_existing_drafts_table(tmp_path) -> None:
    path = tmp_path / "bot.sqlite3"
    async with aiosqlite.connect(path) as db:
        await db.executescript(
            """
            CREATE TABLE settings (
                user_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                channel_title TEXT,
                signature_json TEXT,
                instant_publish INTEGER NOT NULL DEFAULT 0,
                reply_keyboard_removed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE pending_text (
                user_id INTEGER PRIMARY KEY,
                rich_text_json TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                media_json TEXT NOT NULL,
                caption_json TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        await db.commit()
    storage = Storage(path)

    await storage.initialize()

    async with aiosqlite.connect(path) as db:
        rows = await (await db.execute("PRAGMA table_info(drafts)")).fetchall()
        columns = {row[1] for row in rows}
    assert "claimed_at" in columns
