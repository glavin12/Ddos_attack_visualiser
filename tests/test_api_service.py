"""Tests for RadarQueryService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from ddos_attack_project.api.service import RadarQueryService
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    Layer,
    Normalization,
    Unit,
)


def make_service(session_factory, **kwargs) -> RadarQueryService:
    repo = ObservationRepository(session_factory)
    return RadarQueryService(repo, **kwargs)


async def test_overview_l3(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    overview = await service.overview(Layer.L3)

    assert overview.layer == Layer.L3
    assert len(overview.top_routes) == 100
    assert len(overview.top_origins) == 50
    assert len(overview.top_targets) == 50
    assert overview.observation.start is not None
    assert overview.observation.collected_at is not None


async def test_attacks_l3(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    attacks = await service.attacks(Layer.L3)

    assert attacks.layer == Layer.L3
    assert attacks.unit == Unit.BYTES
    assert len(attacks.entries) == 100
    first = attacks.entries[0]
    assert first.source.code == "BR"
    assert first.target.code == "US"
    assert first.share > 0


async def test_attacks_l7_unit(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    attacks = await service.attacks(Layer.L7)

    assert attacks.unit == Unit.REQUESTS
    assert len(attacks.entries) == 100


async def test_countries_origin(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.countries(Layer.L3, DistributionRole.ORIGIN)

    assert response.role == DistributionRole.ORIGIN
    assert len(response.entries) == 50
    assert response.entries[0].country.code == "US"


async def test_countries_target(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.countries(Layer.L7, DistributionRole.TARGET)

    assert response.role == DistributionRole.TARGET
    assert response.unit == Unit.REQUESTS
    assert response.entries[0].country.code == "US"


async def test_characteristics_protocol(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.characteristics(
        Layer.L3, CharacteristicCategory.PROTOCOL
    )

    assert response.type == CharacteristicCategory.PROTOCOL
    assert response.unit == Unit.BYTES
    udp = next(c for c in response.entries if c.value == "UDP")
    assert float(udp.share) > 0.5


async def test_characteristics_http_method(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.characteristics(
        Layer.L7, CharacteristicCategory.HTTP_METHOD
    )

    assert response.unit == Unit.REQUESTS
    get_entry = next(c for c in response.entries if c.value == "GET")
    assert float(get_entry.share) > 0.5


async def test_history_l3(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.history(Layer.L3)

    assert response.normalization == Normalization.MIN0_MAX
    assert response.aggregation == "ONE_HOUR"
    assert len(response.points) == 167
    assert response.points[0].value >= 0


async def test_history_l7_unit(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    response = await service.history(Layer.L7)

    assert response.unit == Unit.REQUESTS
    assert len(response.points) == 167


async def test_status_healthy(seeded_session_factory) -> None:
    service = make_service(seeded_session_factory)
    status = await service.status()

    assert status.status == "healthy"
    assert status.collected_at is not None


async def test_status_degraded_when_no_data(session_factory) -> None:
    service = make_service(session_factory)
    status = await service.status()

    assert status.status == "degraded"
    assert status.collected_at is None


async def test_status_degraded_when_stale(session_factory) -> None:
    from tests.conftest import build_dataset

    service = make_service(
        session_factory,
        stale_after_seconds=3600,
    )
    repo = ObservationRepository(session_factory)
    dataset = build_dataset(
        EndpointKey.L3_TOP_ATTACKS, str(uuid4())
    )
    dataset.observation = dataset.observation.model_copy(
        update={
            "collected_at": datetime.now(UTC) - timedelta(days=2),
        }
    )
    await repo.save_refresh([dataset])
    status = await service.status()
    assert status.status == "degraded"


async def test_empty_responses_when_no_data(session_factory) -> None:
    service = make_service(session_factory)

    overview = await service.overview(Layer.L3)
    attacks = await service.attacks(Layer.L3)
    countries = await service.countries(Layer.L3, DistributionRole.ORIGIN)
    characteristics = await service.characteristics(
        Layer.L3, CharacteristicCategory.VECTOR
    )
    history = await service.history(Layer.L3)

    assert overview.top_routes == []
    assert attacks.entries == []
    assert countries.entries == []
    assert characteristics.entries == []
    assert history.points == []
