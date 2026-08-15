"""Tests for the WebSocket radar stream endpoint (Phase 7)."""

from __future__ import annotations

import pytest_asyncio
from fastapi.testclient import TestClient

from ddos_attack_project.main import create_app

from tests.conftest import seed_full_refresh


@pytest_asyncio.fixture
async def seeded_app(session_factory):
    await seed_full_refresh(session_factory)
    return create_app(session_factory=session_factory)


def _receive_json(websocket) -> dict:
    message = websocket.receive_json()
    assert isinstance(message, dict)
    return message


def test_websocket_connection_and_attack_event(seeded_app) -> None:
    """A connected client receives a valid attack_event envelope."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as websocket:
            message = _receive_json(websocket)
            assert message["type"] in {"attack_event", "stats", "system"}
            if message["type"] == "attack_event":
                data = message["data"]
                assert data["event_id"]
                assert data["layer"] in {"L3", "L7"}
                assert data["source"]["code"]
                assert data["target"]["code"]
                assert 0.0 <= data["intensity"] <= 1.0
                assert data["is_synthetic"] is True
                assert data["data_source"] in {"cloudflare_radar", "synthetic"}


def test_websocket_reconnect(seeded_app) -> None:
    """A client can disconnect and reconnect to resume the stream."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as first:
            message = _receive_json(first)
            assert message["type"] in {"attack_event", "stats", "system"}

        with client.websocket_connect("/api/v1/ws/radar") as second:
            message = _receive_json(second)
            assert message["type"] in {"attack_event", "stats", "system"}


def test_websocket_broadcast_is_synthetic(seeded_app) -> None:
    """Attack events are explicitly marked synthetic (never real telemetry)."""
    with TestClient(seeded_app) as client:
        with client.websocket_connect("/api/v1/ws/radar") as websocket:
            for _ in range(5):
                message = _receive_json(websocket)
                if message["type"] == "attack_event":
                    assert message["data"]["is_synthetic"] is True
