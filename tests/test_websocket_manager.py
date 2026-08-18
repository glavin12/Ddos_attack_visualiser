"""Tests for the WebSocket connection manager."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest_asyncio

from ddos_attack_project.domain.enums import IndicatorType, SourceFeed
from ddos_attack_project.domain.models import ThreatIndicator
from ddos_attack_project.websocket.envelopes import (
    StatsData,
    StatsMessage,
    SystemData,
    SystemMessage,
)
from ddos_attack_project.websocket.manager import ConnectionManager


def _indicator() -> ThreatIndicator:
    now = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)
    return ThreatIndicator(
        source_feed=SourceFeed.FEODO,
        indicator="1.1.1.1",
        indicator_type=IndicatorType.IP,
        resolved_ip="1.1.1.1",
        first_seen=now,
        last_seen=now,
    )


class FakeWebSocket:
    """Minimal stand-in for ``fastapi.WebSocket``."""

    def __init__(self, *, fail_after: int | None = None) -> None:
        self.accepted = False
        self.messages: list[dict] = []
        self._fail_after = fail_after

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        if self._fail_after is not None and len(self.messages) >= self._fail_after:
            raise ConnectionError("socket closed")
        self.messages.append(payload)

    async def receive_text(self) -> str:
        await asyncio.sleep(60)


@pytest_asyncio.fixture
async def manager() -> ConnectionManager:
    return ConnectionManager()


async def test_connect_adds_connection(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    assert socket.accepted
    assert manager.connection_count == 1


async def test_disconnect_removes_connection(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.disconnect(socket)
    assert manager.connection_count == 0


async def test_broadcast_delivers_to_all(manager: ConnectionManager) -> None:
    a = FakeWebSocket()
    b = FakeWebSocket()
    await manager.connect(a)
    await manager.connect(b)
    message = SystemMessage(data=SystemData(message="hello"))

    await manager.broadcast(message)
    assert len(a.messages) == 1
    assert len(b.messages) == 1
    assert a.messages[0] == {"type": "system", "data": {"message": "hello"}}


async def test_broadcast_threat_indicators(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.broadcast_threat_indicators([_indicator()])
    payload = socket.messages[0]
    assert payload["type"] == "threat_indicator"
    assert payload["data"]["indicator"] == "1.1.1.1"


async def test_broadcast_stats(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.broadcast_stats(active_indicators=34)
    payload = socket.messages[0]
    assert payload == {
        "type": "stats",
        "data": {"active_indicators": 34},
    }


async def test_broadcast_drops_dead_connection(manager: ConnectionManager) -> None:
    dead = FakeWebSocket(fail_after=0)
    alive = FakeWebSocket()
    await manager.connect(dead)
    await manager.connect(alive)

    await manager.broadcast(SystemMessage(data=SystemData(message="boom")))
    assert manager.connection_count == 1
    assert len(alive.messages) == 1


async def test_broadcast_stats_uses_stats_message(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.broadcast(StatsMessage(data=StatsData(active_indicators=5)))
    assert socket.messages[0]["data"]["active_indicators"] == 5
