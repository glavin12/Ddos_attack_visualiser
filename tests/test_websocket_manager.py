"""Tests for the WebSocket connection manager."""

from __future__ import annotations

import asyncio

import pytest_asyncio

from ddos_attack_project.domain.enums import Layer
from ddos_attack_project.websocket.envelopes import (
    AttackEventData,
    AttackEventMessage,
    SourceTarget,
    StatsData,
    StatsMessage,
    SystemData,
    SystemMessage,
)
from ddos_attack_project.websocket.manager import ConnectionManager


def attack_event(event_id: str = "e1") -> AttackEventData:
    return AttackEventData(
        event_id=event_id,
        layer=Layer.L3,
        source=SourceTarget(code="US", lat=1.0, lon=2.0),
        target=SourceTarget(code="IN", lat=3.0, lon=4.0),
        intensity=0.72,
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


async def test_broadcast_attacks(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.broadcast(AttackEventMessage(data=attack_event()))
    payload = socket.messages[0]
    assert payload["type"] == "attack_event"
    assert payload["data"]["event_id"] == "e1"


async def test_broadcast_stats(manager: ConnectionManager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    await manager.broadcast_stats(active_events=34)
    payload = socket.messages[0]
    assert payload == {"type": "stats", "data": {"active_events": 34}}


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
    await manager.broadcast(StatsMessage(data=StatsData(active_events=5)))
    assert socket.messages[0]["data"]["active_events"] == 5
