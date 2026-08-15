"""Tests for canonical domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ddos_attack_project.domain.models import (
    AttackCharacteristic,
    AttackPair,
    DistributionEntry,
    RadarObservation,
    TimeSeriesPoint,
)
from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    Layer,
    Normalization,
    Unit,
)


def test_attack_pair_valid() -> None:
    pair = AttackPair(
        layer=Layer.L3,
        source_country_code="BR",
        source_country_name="Brazil",
        target_country_code="US",
        target_country_name="United States",
        share=Decimal("0.06844203"),
        unit=Unit.BYTES,
    )
    assert pair.share == Decimal("0.06844203")
    assert pair.rank is None


def test_attack_pair_rejects_share_over_one() -> None:
    with pytest.raises(ValidationError):
        AttackPair(
            layer=Layer.L3,
            source_country_code="BR",
            target_country_code="US",
            share=Decimal("1.1"),
            unit=Unit.BYTES,
        )


def test_attack_pair_rejects_lowercase_country() -> None:
    with pytest.raises(ValidationError):
        AttackPair(
            layer=Layer.L3,
            source_country_code="br",
            target_country_code="US",
            share=Decimal("0.1"),
            unit=Unit.BYTES,
        )


def test_attack_pair_accepts_rank() -> None:
    pair = AttackPair(
        layer=Layer.L7,
        source_country_code="US",
        target_country_code="US",
        share=Decimal("0.16"),
        rank=1,
        unit=Unit.REQUESTS,
    )
    assert pair.rank == 1


def test_distribution_entry_origin() -> None:
    entry = DistributionEntry(
        layer=Layer.L3,
        role=DistributionRole.ORIGIN,
        country_code="US",
        country_name="United States",
        share=Decimal("0.1649"),
        rank=1,
        unit=Unit.BYTES,
    )
    assert entry.role == DistributionRole.ORIGIN


def test_attack_characteristic_valid() -> None:
    characteristic = AttackCharacteristic(
        layer=Layer.L3,
        category=CharacteristicCategory.VECTOR,
        value="SYN Flood",
        share=Decimal("0.2225"),
        unit=Unit.BYTES,
    )
    assert characteristic.category == CharacteristicCategory.VECTOR


def test_timeseries_point_value_range() -> None:
    with pytest.raises(ValidationError):
        TimeSeriesPoint(
            layer=Layer.L3,
            timestamp=datetime.now(UTC),
            value=1.5,
            unit=Unit.BYTES,
        )


def test_timeseries_point_defaults_to_min0max() -> None:
    point = TimeSeriesPoint(
        layer=Layer.L7,
        timestamp=datetime.now(UTC),
        value=0.82,
        unit=Unit.REQUESTS,
    )
    assert point.normalization == Normalization.MIN0_MAX


def test_radar_observation_valid() -> None:
    observation = RadarObservation(
        refresh_id=uuid4(),
        endpoint_key=EndpointKey.L3_TOP_ATTACKS,
        layer=Layer.L3,
        collected_at=datetime.now(UTC),
        window_start=datetime.now(UTC),
        window_end=datetime.now(UTC),
        cloudflare_last_updated=datetime.now(UTC),
        normalization=Normalization.PERCENTAGE,
        unit=Unit.BYTES,
    )
    assert observation.endpoint_key == EndpointKey.L3_TOP_ATTACKS
