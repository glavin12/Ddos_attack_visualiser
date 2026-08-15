"""Tests for REST API response schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import ValidationError
import pytest

from ddos_attack_project.api.schemas import (
    AttacksResponse,
    CharacteristicsResponse,
    CountriesResponse,
    HealthResponse,
    HistoryResponse,
    OverviewResponse,
)
from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    Layer,
    Normalization,
    Unit,
)


def test_health_response() -> None:
    response = HealthResponse()
    assert response.status == "ok"


def test_attacks_response_contract() -> None:
    response = AttacksResponse(
        layer=Layer.L3,
        unit=Unit.BYTES,
        entries=[
            {
                "source": {"code": "BR", "name": "Brazil"},
                "target": {"code": "US", "name": "United States"},
                "share": Decimal("0.06844203"),
            }
        ],
    )
    assert response.entries[0].share == Decimal("0.06844203")
    assert response.entries[0].rank is None


def test_attacks_response_rejects_invalid_share() -> None:
    with pytest.raises(ValidationError):
        AttacksResponse(
            layer=Layer.L3,
            unit=Unit.BYTES,
            entries=[
                {
                    "source": {"code": "BR"},
                    "target": {"code": "US"},
                    "share": Decimal("1.5"),
                }
            ],
        )


def test_countries_response_contract() -> None:
    response = CountriesResponse(
        layer=Layer.L7,
        role=DistributionRole.TARGET,
        unit=Unit.REQUESTS,
        entries=[
            {"country": {"code": "US", "name": "United States"}, "share": Decimal("0.5088"), "rank": 1}
        ],
    )
    assert response.role == DistributionRole.TARGET


def test_characteristics_response_contract() -> None:
    response = CharacteristicsResponse(
        layer=Layer.L3,
        type=CharacteristicCategory.PROTOCOL,
        unit=Unit.BYTES,
        entries=[{"value": "UDP", "share": Decimal("0.7632")}],
    )
    assert response.entries[0].value == "UDP"


def test_history_response_contract() -> None:
    response = HistoryResponse(
        layer=Layer.L3,
        unit=Unit.BYTES,
        normalization=Normalization.MIN0_MAX,
        aggregation="ONE_HOUR",
        points=[
            {"timestamp": "2026-08-15T05:00:00Z", "value": 0.112243},
        ],
    )
    assert response.points[0].value == 0.112243


def test_overview_response_contract() -> None:
    response = OverviewResponse(
        observation={
            "start": "2026-08-14T09:00:00Z",
            "end": "2026-08-15T09:00:00Z",
            "last_updated": "2026-08-15T08:15:00Z",
            "collected_at": "2026-08-15T08:16:00Z",
        },
        layer=Layer.L3,
        top_routes=[
            {
                "source": {"code": "BR"},
                "target": {"code": "US"},
                "share": Decimal("0.0684"),
            }
        ],
        top_origins=[],
        top_targets=[],
    )
    assert response.observation.start is not None
    assert len(response.top_routes) == 1
