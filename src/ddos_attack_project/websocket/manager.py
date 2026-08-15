"""WebSocket connection manager and broadcast hub.

Single central manager per application instance (IMPLEMENTATION 15). It
tracks active connections, broadcasts serialized messages, removes dead
clients, and exposes stats/system helpers used by the scheduler and app.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from ddos_attack_project.websocket.envelopes import (
    StatsData,
    StatsMessage,
    SystemData,
    SystemMessage,
)


@dataclass
class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts messages."""

    connections: set[WebSocket] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def connection_count(self) -> int:
        return len(self.connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.connections.discard(websocket)

    async def broadcast(self, message: Any) -> None:
        """Send ``message`` to every connection, dropping dead ones."""
        async with self._lock:
            snapshot = list(self.connections)
        dead: list[WebSocket] = []
        for websocket in snapshot:
            try:
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            await self.disconnect(websocket)

    async def broadcast_stats(self, active_events: int) -> None:
        await self.broadcast(
            StatsMessage(data=StatsData(active_events=active_events))
        )

    async def broadcast_system(self, message: str) -> None:
        await self.broadcast(SystemMessage(data=SystemData(message=message)))


__all__ = ["ConnectionManager"]
