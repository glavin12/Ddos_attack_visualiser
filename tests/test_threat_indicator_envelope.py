"""Tests for the ThreatIndicator WebSocket envelope + broadcast."""

from __future__ import annotations

from datetime import UTC, datetime

from ddos_attack_project.domain.enums import IndicatorType, SourceFeed
from ddos_attack_project.domain.models import ThreatIndicator
from ddos_attack_project.websocket.envelopes import (
    ThreatIndicatorData,
    ThreatIndicatorMessage,
)
from ddos_attack_project.websocket.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


def _indicator() -> ThreatIndicator:
    now = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)
    return ThreatIndicator(
        source_feed=SourceFeed.FEODO,
        indicator="185.220.101.42",
        indicator_type=IndicatorType.IP,
        resolved_ip="185.220.101.42",
        country_code="NL",
        country_name="Netherlands",
        city="Rotterdam",
        latitude=51.92,
        longitude=4.48,
        threat_family="Emotet",
        first_seen=now,
        last_seen=now,
        source_url="https://feodotracker.abuse.ch/browse/host/185.220.101.42/",
    )


def test_threat_indicator_message_shape() -> None:
    message = ThreatIndicatorMessage(
        data=ThreatIndicatorData.from_domain(_indicator())
    )
    payload = message.model_dump(mode="json")
    assert payload["type"] == "threat_indicator"
    data = payload["data"]
    assert data["indicator"] == "185.220.101.42"
    assert data["source_feed"] == "feodo"
    assert data["threat_family"] == "Emotet"
    assert data["city"] == "Rotterdam"
    assert data["lat"] == 51.92
    assert data["lng"] == 4.48
    assert "greynoise_classification" in data


async def test_broadcast_threat_indicators_sends_one_message_per_indicator() -> None:
    manager = ConnectionManager()
    socket = FakeWebSocket()
    await manager.connect(socket)

    await manager.broadcast_threat_indicators([_indicator(), _indicator()])
    assert len(socket.messages) == 2
    for payload in socket.messages:
        assert payload["type"] == "threat_indicator"
        assert payload["data"]["indicator"] == "185.220.101.42"


async def test_indicator_with_no_geolocation_serializes_null_fields() -> None:
    partial = ThreatIndicator(
        source_feed=SourceFeed.URLHAUS,
        indicator="http://x.example/",
        indicator_type=IndicatorType.URL,
        resolved_ip="0.0.0.0",
        first_seen=datetime(2026, 8, 19, 14, 0, tzinfo=UTC),
        last_seen=datetime(2026, 8, 19, 14, 0, tzinfo=UTC),
    )
    payload = ThreatIndicatorMessage(
        data=ThreatIndicatorData.from_domain(partial)
    ).model_dump(mode="json")
    data = payload["data"]
    assert data["country_code"] is None
    assert data["city"] is None
    assert data["lat"] is None
    assert data["lng"] is None
