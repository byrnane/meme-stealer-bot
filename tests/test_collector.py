import asyncio
from types import SimpleNamespace

from meme_stealer_bot.collector import AlbumCollector


async def test_album_collector_groups_and_sorts_messages() -> None:
    received = []

    async def on_album(messages):
        received.append(messages)

    collector = AlbumCollector(on_album, delay=0.01)
    await collector.add(SimpleNamespace(media_group_id="group", message_id=2))
    await collector.add(SimpleNamespace(media_group_id="group", message_id=1))
    await asyncio.sleep(0.03)

    assert [[message.message_id for message in album] for album in received] == [[1, 2]]
