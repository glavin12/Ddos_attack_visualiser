"""Tests for the WebSocket radar stream endpoint."""

from __future__ import annotations

import pytest_asyncio
from fastapi.testclient import TestClient

from ddos_attack_project.main import create_app

from tests.conftest import NullIngestor, seed_full_refresh


@pytest_asyncio.fixture
async def seeded_app(session_factory):
    await seed_full_refresh(session_factory)
    return create_app(
        session_factory=session_factory,
        ingestor=NullIngestor(),
        threatintel_ingestor=NullIngestor(),
    )


def _receive_json(websocket) -> dict:
    message = websocket.receive_json()
    assert isinstance(message, dict)
    return message


def test_websocket_sends_welcome_on_connect(seeded_app) -> None:
    """A connected client immediately receives the welcome system envelope."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as websocket:
            message = _receive_json(websocket)
            assert message["type"] == "system"
            assert "Threat Observatory" in message["data"]["message"]


def test_websocket_reconnect(seeded_app) -> None:
    """A client can disconnect and reconnect to resume the stream."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as first:
            _receive_json(first)  # welcome
        with client.websocket_connect("/api/v1/ws/radar") as second:
            message = _receive_json(second)
            assert message["type"] == "system"


def test_websocket_sends_pulse_after_welcome(seeded_app) -> None:
    """A connected client immediately receives the latest 24h aggregates."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as websocket:
            welcome = _receive_json(websocket)
            assert welcome["type"] == "system"

            pulse = _receive_json(websocket)
            assert pulse["type"] == "radar_pulse"
            assert pulse["data"]["l3"]["routes"]
            assert pulse["data"]["l7"]["routes"]
            first_route = pulse["data"]["l3"]["routes"][0]
            assert {"code", "name"} <= set(first_route["source"])
            assert isinstance(first_route["share"], float)
            assert pulse["data"]["l3"]["collected_at"] is not None
