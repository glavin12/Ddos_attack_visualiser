"""Tests for WebSocket envelope models."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from ddos_attack_project.websocket.envelopes import (
    AttackEventMessage,
    StatsMessage,
    SystemMessage,
    WebSocketMessage,
)


def test_attack_event_envelope_parses() -> None:
    raw = {
        "type": "attack_event",
        "data": {
            "event_id": "123e4567-e89b-12d3-a456-426614174000",
            "layer": "L3",
            "source": {"code": "US", "name": "United States", "lat": 40.0, "lon": -98.0},
            "target": {"code": "IN", "name": "India", "lat": 20.0, "lon": 78.0},
            "intensity": 0.72,
            "is_synthetic": True,
            "data_source": "cloudflare_radar",
        },
    }
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, AttackEventMessage)
    assert message.data.data_source == "cloudflare_radar"


def test_stats_envelope_parses() -> None:
    raw = {"type": "stats", "data": {"active_events": 34}}
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, StatsMessage)
    assert message.data.active_events == 34


def test_system_envelope_parses() -> None:
    raw = {"type": "system", "data": {"message": "Radar dataset refreshed"}}
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, SystemMessage)


def test_unknown_type_rejected() -> None:
    raw = {"type": "unknown", "data": {}}
    with pytest.raises(ValidationError):
        TypeAdapter(WebSocketMessage).validate_python(raw)


def test_attack_event_rejects_invalid_intensity() -> None:
    raw = {
        "type": "attack_event",
        "data": {
            "event_id": "123e4567-e89b-12d3-a456-426614174000",
            "layer": "L3",
            "source": {"code": "US", "lat": 40.0, "lon": -98.0},
            "target": {"code": "IN", "lat": 20.0, "lon": 78.0},
            "intensity": 2.0,
        },
    }
    with pytest.raises(ValidationError):
        TypeAdapter(WebSocketMessage).validate_python(raw)
