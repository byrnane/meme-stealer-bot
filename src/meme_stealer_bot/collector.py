from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from aiogram.types import Message


class AlbumCollector:
    def __init__(
        self,
        on_album: Callable[[list[Message]], Awaitable[None]],
        delay: float = 0.8,
    ) -> None:
        self.on_album = on_album
        self.delay = delay
        self._messages: dict[str, list[Message]] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def add(self, message: Message) -> None:
        group_id = message.media_group_id
        if not group_id:
            raise ValueError("Message does not belong to a media group")
        async with self._lock:
            self._messages.setdefault(group_id, []).append(message)
            old_task = self._tasks.get(group_id)
            if old_task:
                old_task.cancel()
            self._tasks[group_id] = asyncio.create_task(self._flush_later(group_id))

    async def _flush_later(self, group_id: str) -> None:
        try:
            await asyncio.sleep(self.delay)
            async with self._lock:
                messages = sorted(
                    self._messages.pop(group_id, []), key=lambda item: item.message_id
                )
                self._tasks.pop(group_id, None)
            if messages:
                await self.on_album(messages)
        except asyncio.CancelledError:
            return
