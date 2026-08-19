"""WebSocket connection manager and broadcast hub.

Single central manager per application instance. It tracks active
connections, broadcasts serialized messages, removes dead clients, and
exposes helpers used by the threat-intel ingestor and lifespan hooks.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from ddos_attack_project.domain.models import ThreatIndicator
from ddos_attack_project.websocket.envelopes import (
    RadarPulseData,
    RadarPulseMessage,
    StatsData,
    StatsMessage,
    SystemData,
    SystemMessage,
    ThreatIndicatorData,
    ThreatIndicatorMessage,
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

    async def send_to(self, websocket: WebSocket, message: Any) -> None:
        """Send one message to a single connection (used for welcome banners)."""
        try:
            await websocket.send_json(message.model_dump(mode="json"))
        except Exception:
            await self.disconnect(websocket)

    async def broadcast_stats(self, *, active_indicators: int = 0) -> None:
        await self.broadcast(
            StatsMessage(data=StatsData(active_indicators=active_indicators))
        )

    async def broadcast_system(self, message: str) -> None:
        await self.broadcast(SystemMessage(data=SystemData(message=message)))

    async def broadcast_threat_indicators(
        self, indicators: list[ThreatIndicator]
    ) -> None:
        """Broadcast one ``threat_indicator`` message per new IOC."""
        for indicator in indicators:
            await self.broadcast(
                ThreatIndicatorMessage(
                    data=ThreatIndicatorData.from_domain(indicator)
                )
            )

    async def broadcast_radar_pulse(self, data: RadarPulseData) -> None:
        """Broadcast the latest Radar 24h aggregates to every client."""
        await self.broadcast(RadarPulseMessage(data=data))


__all__ = ["ConnectionManager"]
