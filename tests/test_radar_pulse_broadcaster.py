"""Tests for the RadarPulseBroadcaster."""

from __future__ import annotations

import asyncio

import pytest_asyncio

from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.websocket.manager import ConnectionManager
from ddos_attack_project.websocket.pulse import RadarPulseBroadcaster

from tests.test_websocket_manager import FakeWebSocket


@pytest_asyncio.fixture
async def seeded_repo(seeded_session_factory) -> ObservationRepository:
    return ObservationRepository(seeded_session_factory)


@pytest_asyncio.fixture
async def manager() -> ConnectionManager:
    return ConnectionManager()


def _broadcaster(
    repo: ObservationRepository,
    manager: ConnectionManager,
    **kwargs,
) -> RadarPulseBroadcaster:
    return RadarPulseBroadcaster(repo, manager, **kwargs)


async def test_pulse_once_with_no_data_sends_nothing(
    session_factory, manager
) -> None:
    """No persisted observation for either layer → no broadcast, ever."""
    repo = ObservationRepository(session_factory)
    socket = FakeWebSocket()
    await manager.connect(socket)
    broadcaster = _broadcaster(repo, manager)

    result = await broadcaster.pulse_once()

    assert result is None
    assert socket.messages == []


async def test_pulse_once_broadcasts_both_layers(seeded_repo, manager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    broadcaster = _broadcaster(seeded_repo, manager)

    result = await broadcaster.pulse_once()

    assert result is not None
    assert result.l3 is not None and result.l3.routes
    assert result.l7 is not None and result.l7.routes
    assert len(socket.messages) == 1
    payload = socket.messages[0]
    assert payload["type"] == "radar_pulse"
    assert payload["data"]["l3"]["routes"][0]["source"]["code"]
    assert payload["data"]["l3"]["collected_at"] is not None
    # Routes arrive share-ranked (repository orders by share desc).
    shares = [r["share"] for r in payload["data"]["l3"]["routes"]]
    assert shares == sorted(shares, reverse=True)


async def test_pulse_respects_max_routes_cap(seeded_repo, manager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    broadcaster = _broadcaster(
        seeded_repo, manager, max_routes_per_layer=2
    )

    result = await broadcaster.pulse_once()

    assert result is not None
    assert len(result.l3.routes) <= 2
    assert len(result.l7.routes) <= 2


async def test_on_radar_refresh_broadcasts(seeded_repo, manager) -> None:
    """The ingestor's on_refresh hook pulses immediately."""
    socket = FakeWebSocket()
    await manager.connect(socket)
    broadcaster = _broadcaster(seeded_repo, manager)

    await broadcaster.on_radar_refresh("some-refresh-id")

    assert len(socket.messages) == 1
    assert socket.messages[0]["type"] == "radar_pulse"


async def test_send_to_delivers_pulse_to_single_client(
    seeded_repo, manager
) -> None:
    solo = FakeWebSocket()
    other = FakeWebSocket()
    await manager.connect(solo)
    await manager.connect(other)
    broadcaster = _broadcaster(seeded_repo, manager)

    await broadcaster.send_to(solo)

    assert len(solo.messages) == 1
    assert solo.messages[0]["type"] == "radar_pulse"
    assert other.messages == []


class _SpyRepo:
    """Counts latest_observation calls to prove the idle loop skips the DB."""

    def __init__(self, inner: ObservationRepository) -> None:
        self._inner = inner
        self.latest_observation_calls = 0

    async def latest_observation(self, *args, **kwargs):
        self.latest_observation_calls += 1
        return await self._inner.latest_observation(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)


async def test_heartbeat_skips_db_without_connections(
    seeded_repo, manager
) -> None:
    spy = _SpyRepo(seeded_repo)
    broadcaster = _broadcaster(spy, manager, interval_seconds=0.05)

    await broadcaster.start()
    await asyncio.sleep(0.25)
    await broadcaster.stop()

    assert spy.latest_observation_calls == 0


async def test_heartbeat_pulses_with_connections(seeded_repo, manager) -> None:
    socket = FakeWebSocket()
    await manager.connect(socket)
    spy = _SpyRepo(seeded_repo)
    broadcaster = _broadcaster(spy, manager, interval_seconds=0.05)

    await broadcaster.start()
    await asyncio.sleep(0.25)
    await broadcaster.stop()

    assert spy.latest_observation_calls > 0
    pulses = [m for m in socket.messages if m["type"] == "radar_pulse"]
    assert pulses


async def test_start_stop_is_clean(seeded_repo, manager) -> None:
    broadcaster = _broadcaster(seeded_repo, manager)
    await broadcaster.start()
    await broadcaster.stop()
    # A second run after stop must be possible (task was cleared).
    await broadcaster.start()
    await broadcaster.stop()
