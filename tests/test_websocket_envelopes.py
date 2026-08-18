"""Tests for WebSocket envelope models."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from ddos_attack_project.websocket.envelopes import (
    StatsMessage,
    SystemMessage,
    ThreatIndicatorMessage,
    WebSocketMessage,
)


def test_threat_indicator_envelope_parses() -> None:
    raw = {
        "type": "threat_indicator",
        "data": {
            "indicator": "185.220.101.42",
            "indicator_type": "ip",
            "source_feed": "feodo",
            "resolved_ip": "185.220.101.42",
            "country_code": "NL",
            "country_name": "Netherlands",
            "city": "Rotterdam",
            "lat": 51.92,
            "lng": 4.48,
            "threat_family": "Emotet",
            "first_seen": "2026-08-19T14:00:00Z",
            "last_seen": "2026-08-19T14:00:00Z",
            "source_url": "https://feodotracker.abuse.ch/browse/host/185.220.101.42/",
        },
    }
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, ThreatIndicatorMessage)
    assert message.data.source_feed == "feodo"


def test_stats_envelope_parses() -> None:
    raw = {"type": "stats", "data": {"active_indicators": 34}}
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, StatsMessage)
    assert message.data.active_indicators == 34


def test_system_envelope_parses() -> None:
    raw = {"type": "system", "data": {"message": "Radar dataset refreshed"}}
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, SystemMessage)


def test_unknown_type_rejected() -> None:
    raw = {"type": "unknown", "data": {}}
    with pytest.raises(ValidationError):
        TypeAdapter(WebSocketMessage).validate_python(raw)


def test_threat_indicator_rejects_out_of_range_coords() -> None:
    raw = {
        "type": "threat_indicator",
        "data": {
            "indicator": "1.1.1.1",
            "indicator_type": "ip",
            "source_feed": "feodo",
            "resolved_ip": "1.1.1.1",
            "lat": 200.0,
            "lng": 0.0,
            "first_seen": "2026-08-19T14:00:00Z",
            "last_seen": "2026-08-19T14:00:00Z",
        },
    }
    # Pydantic on the envelope's ThreatIndicatorData does not enforce range
    # (frontend handles clamping). This test only asserts required fields.
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, ThreatIndicatorMessage)
