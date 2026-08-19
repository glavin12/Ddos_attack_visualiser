"""Tests for the radar_pulse WebSocket envelope."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from ddos_attack_project.api.schemas import AttackRoute, CountryRef
from ddos_attack_project.websocket.envelopes import (
    RadarPulseData,
    RadarPulseLayerData,
    RadarPulseMessage,
    RadarPulseRoute,
    WebSocketMessage,
)


def _pulse_message() -> RadarPulseMessage:
    return RadarPulseMessage(
        data=RadarPulseData(
            l3=RadarPulseLayerData(
                collected_at="2026-08-20T12:00:00Z",
                observation_start="2026-08-19T12:00:00Z",
                observation_end="2026-08-20T12:00:00Z",
                routes=[
                    RadarPulseRoute(
                        source={"code": "CN", "name": "China"},
                        target={"code": "US", "name": "United States"},
                        share=0.18,
                        rank=1,
                    )
                ],
            ),
            l7=None,
        )
    )


def test_radar_pulse_envelope_parses() -> None:
    raw = _pulse_message().model_dump(mode="json")
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, RadarPulseMessage)
    assert message.data.l3 is not None
    assert message.data.l3.routes[0].source.code == "CN"
    assert message.data.l3.routes[0].share == 0.18
    assert message.data.l7 is None


def test_radar_pulse_empty_data_parses() -> None:
    raw = {"type": "radar_pulse", "data": {}}
    message = TypeAdapter(WebSocketMessage).validate_python(raw)
    assert isinstance(message, RadarPulseMessage)
    assert message.data.l3 is None
    assert message.data.l7 is None


def test_radar_pulse_share_serializes_as_json_number() -> None:
    """The WS manager serializes with model_dump(mode='json'); Decimal would
    emit a string there and break the frontend's ``share: number`` contract,
    so the pulse route must carry a plain float."""
    payload = _pulse_message().model_dump(mode="json")
    share = payload["data"]["l3"]["routes"][0]["share"]
    assert isinstance(share, float)
    assert share == 0.18


def test_pulse_route_shape_matches_rest_attack_route() -> None:
    pulse_route = _pulse_message().data.l3.routes[0].model_dump(mode="json")
    rest_route = AttackRoute(
        source=CountryRef(code="CN", name="China"),
        target=CountryRef(code="US", name="United States"),
        share="0.18",
        rank=1,
    ).model_dump(mode="json")
    assert set(pulse_route) == set(rest_route)
    assert set(pulse_route["source"]) == set(rest_route["source"])
    assert set(pulse_route["target"]) == set(rest_route["target"])


def test_radar_pulse_rejects_out_of_range_share() -> None:
    raw = {
        "type": "radar_pulse",
        "data": {
            "l3": {
                "routes": [
                    {
                        "source": {"code": "CN"},
                        "target": {"code": "US"},
                        "share": 1.5,
                    }
                ]
            }
        },
    }
    with pytest.raises(ValidationError):
        TypeAdapter(WebSocketMessage).validate_python(raw)
