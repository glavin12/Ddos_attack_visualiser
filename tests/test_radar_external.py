"""Tests for Cloudflare external response models against captured fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
)

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"


def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    assert path.exists(), f"missing fixture {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_envelope_parses_common_fields() -> None:
    data = load_fixture("layer3-top-attacks")
    envelope = CloudflareEnvelope.model_validate(data)
    assert envelope.success is True
    assert envelope.errors == []
    assert "top_0" in envelope.result


@pytest.mark.parametrize(
    "fixture",
    [
        "layer3-top-attacks",
        "layer7-top-attacks",
        "layer3-top-origin",
        "layer3-top-target",
        "layer7-top-origin",
        "layer7-top-target",
        "layer3-summary-protocol",
        "layer3-summary-vector",
        "layer7-summary-http-method",
        "layer3-timeseries",
        "layer7-timeseries",
    ],
)
def test_all_fixtures_parse(fixture: str) -> None:
    data = load_fixture(fixture)
    envelope = CloudflareEnvelope.model_validate(data)
    assert envelope.success is True


def test_top_attacks_layer3_parse_without_rank() -> None:
    data = load_fixture("layer3-top-attacks")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTopAttacksResult.model_validate(envelope.result)

    assert len(result.top_0) == 100
    first = result.top_0[0]
    assert first.origin_country_alpha2 == "BR"
    assert first.target_country_alpha2 == "US"
    assert first.rank is None
    assert float(first.value) > 0


def test_top_attacks_layer7_parse_with_rank() -> None:
    data = load_fixture("layer7-top-attacks")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTopAttacksResult.model_validate(envelope.result)

    assert len(result.top_0) == 100
    first = result.top_0[0]
    assert first.rank is not None
    assert first.rank >= 1


def test_top_locations_layer3_origin() -> None:
    data = load_fixture("layer3-top-origin")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTopLocationsResult.model_validate(envelope.result)

    assert len(result.top_0) == 50
    first = result.top_0[0]
    assert first.origin_country_alpha2 == "US"
    assert first.target_country_alpha2 is None


def test_top_locations_layer7_target() -> None:
    data = load_fixture("layer7-top-target")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTopLocationsResult.model_validate(envelope.result)

    assert len(result.top_0) == 50
    first = result.top_0[0]
    assert first.target_country_alpha2 == "US"
    assert first.origin_country_alpha2 is None


def test_summary_protocol_parses_percentage_map() -> None:
    data = load_fixture("layer3-summary-protocol")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareSummaryResult.model_validate(envelope.result)

    assert "UDP" in result.summary_0
    assert result.meta is not None
    assert result.meta.normalization == "PERCENTAGE"
    assert result.meta.units[0].value == "bytes"


def test_summary_vector_parses() -> None:
    data = load_fixture("layer3-summary-vector")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareSummaryResult.model_validate(envelope.result)

    assert "Mirai (UDP) Flood" in result.summary_0


def test_summary_http_method_parses() -> None:
    data = load_fixture("layer7-summary-http-method")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareSummaryResult.model_validate(envelope.result)

    assert "GET" in result.summary_0


def test_timeseries_layer3_parses() -> None:
    data = load_fixture("layer3-timeseries")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTimeSeriesResult.model_validate(envelope.result)

    assert len(result.serie_0.timestamps) == len(result.serie_0.values) == 167
    assert result.meta is not None
    assert result.meta.normalization == "MIN0_MAX"
    assert result.meta.agg_interval == "ONE_HOUR"


def test_timeseries_layer7_parses() -> None:
    data = load_fixture("layer7-timeseries")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTimeSeriesResult.model_validate(envelope.result)

    assert len(result.serie_0.timestamps) == 167
    assert result.meta.units[0].value == "requests"
