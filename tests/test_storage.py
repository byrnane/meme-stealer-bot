from datetime import UTC, datetime, timedelta

import aiosqlite

from meme_stealer_bot.models import RichText
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


async def test_pending_details_and_draft_count(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()
    await storage.set_pending_text(1, RichText("текст", []))

    details = await storage.get_pending_text_details(1)

    assert details is not None
    assert details[0] == RichText("текст", [])
    assert details[1] > datetime.now(UTC)
    assert await storage.count_drafts(1) == 0


async def test_reply_keyboard_removal_is_persisted(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    await storage.initialize()

    await storage.mark_reply_keyboard_removed(1)

    assert (await storage.get_settings(1)).reply_keyboard_removed is True
