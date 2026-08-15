"""Tests for the Cloudflare adapters against captured fixtures."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    Normalization,
    Unit,
)
from ddos_attack_project.radar.adapters import adapt
from ddos_attack_project.radar.adapters.common import (
    NormalizationError,
    percentage_to_share,
)
from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
)

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"

_COLLECTED_AT = datetime.now(UTC)
_REFRESH_ID = str(uuid4())

_RESULT_ADAPTERS = {
    EndpointKey.L3_TOP_ATTACKS: TypeAdapter(CloudflareTopAttacksResult),
    EndpointKey.L7_TOP_ATTACKS: TypeAdapter(CloudflareTopAttacksResult),
    EndpointKey.L3_TOP_ORIGIN: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L3_TOP_TARGET: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L7_TOP_ORIGIN: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L7_TOP_TARGET: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L3_SUMMARY_PROTOCOL: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L3_SUMMARY_VECTOR: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L7_SUMMARY_HTTP_METHOD: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L3_TIMESERIES: TypeAdapter(CloudflareTimeSeriesResult),
    EndpointKey.L7_TIMESERIES: TypeAdapter(CloudflareTimeSeriesResult),
}


def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    assert path.exists(), f"missing fixture {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def adapt_fixture(endpoint_key: EndpointKey):
    data = load_fixture(endpoint_key.value)
    envelope = CloudflareEnvelope.model_validate(data)
    result = _RESULT_ADAPTERS[endpoint_key].validate_python(envelope.result)
    return adapt(
        endpoint_key,
        result,
        refresh_id=_REFRESH_ID,
        collected_at=_COLLECTED_AT,
    )


# ---------------------------------------------------------------------------
# Percentage conversion
# ---------------------------------------------------------------------------


def test_percentage_to_share() -> None:
    assert float(percentage_to_share("6.844203")) == pytest.approx(0.06844203)
    assert percentage_to_share("100") == 1
    assert percentage_to_share("0") == 0


def test_percentage_to_share_rejects_invalid() -> None:
    with pytest.raises(NormalizationError):
        percentage_to_share("not-a-number")
    with pytest.raises(NormalizationError):
        percentage_to_share("150")


def test_percentage_to_share_rejects_non_string() -> None:
    with pytest.raises(NormalizationError):
        percentage_to_share(6.8)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Attack pairs
# ---------------------------------------------------------------------------


def test_layer3_top_attacks_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L3_TOP_ATTACKS)

    assert len(dataset.pairs) == 100
    assert dataset.observation.endpoint_key == EndpointKey.L3_TOP_ATTACKS
    assert dataset.observation.unit == Unit.BYTES
    assert dataset.observation.normalization == Normalization.PERCENTAGE
    assert dataset.observation.window_start is not None

    first = dataset.pairs[0]
    assert first.source_country_code == "BR"
    assert first.target_country_code == "US"
    assert 0 < first.share <= 1
    assert first.rank is None


def test_layer7_top_attacks_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L7_TOP_ATTACKS)

    assert len(dataset.pairs) == 100
    assert dataset.observation.unit == Unit.REQUESTS
    assert dataset.pairs[0].rank == 1


# ---------------------------------------------------------------------------
# Country distributions
# ---------------------------------------------------------------------------


def test_layer3_top_origin_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L3_TOP_ORIGIN)

    assert len(dataset.distributions) == 50
    assert dataset.observation.unit == Unit.BYTES
    first = dataset.distributions[0]
    assert first.role == DistributionRole.ORIGIN
    assert first.country_code == "US"
    assert first.rank == 1


def test_layer7_top_target_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L7_TOP_TARGET)

    assert len(dataset.distributions) == 50
    assert dataset.observation.unit == Unit.REQUESTS
    first = dataset.distributions[0]
    assert first.role == DistributionRole.TARGET
    assert first.country_code == "US"
    assert first.rank == 1


# ---------------------------------------------------------------------------
# Characteristics
# ---------------------------------------------------------------------------


def test_layer3_summary_protocol_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L3_SUMMARY_PROTOCOL)

    assert len(dataset.characteristics) == 4
    assert dataset.observation.unit == Unit.BYTES
    udp = next(
        c for c in dataset.characteristics if c.value == "UDP"
    )
    assert udp.category == CharacteristicCategory.PROTOCOL
    assert float(udp.share) == pytest.approx(0.76322904)


def test_layer3_summary_vector_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L3_SUMMARY_VECTOR)

    assert len(dataset.characteristics) == 10
    vector_values = {c.value for c in dataset.characteristics}
    assert "Mirai (UDP) Flood" in vector_values
    assert all(
        c.category == CharacteristicCategory.VECTOR
        for c in dataset.characteristics
    )


def test_layer7_summary_http_method_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L7_SUMMARY_HTTP_METHOD)

    assert len(dataset.characteristics) == 10
    assert dataset.observation.unit == Unit.REQUESTS
    assert all(
        c.category == CharacteristicCategory.HTTP_METHOD
        for c in dataset.characteristics
    )


# ---------------------------------------------------------------------------
# Timeseries
# ---------------------------------------------------------------------------


def test_layer3_timeseries_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L3_TIMESERIES)

    assert len(dataset.timeseries) == 167
    assert dataset.observation.normalization == Normalization.MIN0_MAX
    assert dataset.observation.unit == Unit.BYTES
    assert dataset.timeseries[0].value == pytest.approx(0.06777)
    assert dataset.timeseries[-1].value == pytest.approx(0.519944)


def test_layer7_timeseries_adapted() -> None:
    dataset = adapt_fixture(EndpointKey.L7_TIMESERIES)

    assert len(dataset.timeseries) == 167
    assert dataset.observation.unit == Unit.REQUESTS
    assert dataset.timeseries[-1].value == pytest.approx(0.854864)


def test_timeseries_values_not_divided_by_100() -> None:
    # MIN0_MAX values must be preserved as-is, not treated as percentages.
    dataset = adapt_fixture(EndpointKey.L3_TIMESERIES)
    raw_first = 0.06777
    assert dataset.timeseries[0].value == pytest.approx(raw_first)
