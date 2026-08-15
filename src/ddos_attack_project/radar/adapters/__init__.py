"""Cloudflare response adapters.

Each adapter is the strict boundary between Cloudflare's API format and the
application's canonical domain models.
"""

from __future__ import annotations

from datetime import datetime

from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    Normalization,
    Unit,
)
from ddos_attack_project.domain.models import RadarDataset
from ddos_attack_project.radar.adapters.attacks import adapt_attack_pairs
from ddos_attack_project.radar.adapters.characteristics import (
    adapt_characteristics,
)
from ddos_attack_project.radar.adapters.common import build_observation
from ddos_attack_project.radar.adapters.locations import adapt_distributions
from ddos_attack_project.radar.adapters.timeseries import adapt_timeseries
from ddos_attack_project.radar.external import (
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
)

# Per-endpoint defaults for metadata that Cloudflare may omit.
_ENDPOINT_LAYER = {
    EndpointKey.L3_TOP_ATTACKS: "L3",
    EndpointKey.L7_TOP_ATTACKS: "L7",
    EndpointKey.L3_TOP_ORIGIN: "L3",
    EndpointKey.L3_TOP_TARGET: "L3",
    EndpointKey.L7_TOP_ORIGIN: "L7",
    EndpointKey.L7_TOP_TARGET: "L7",
    EndpointKey.L3_SUMMARY_PROTOCOL: "L3",
    EndpointKey.L3_SUMMARY_VECTOR: "L3",
    EndpointKey.L7_SUMMARY_HTTP_METHOD: "L7",
    EndpointKey.L3_TIMESERIES: "L3",
    EndpointKey.L7_TIMESERIES: "L7",
}

_ENDPOINT_UNIT = {
    EndpointKey.L3_TOP_ATTACKS: Unit.BYTES,
    EndpointKey.L7_TOP_ATTACKS: Unit.REQUESTS,
    EndpointKey.L3_TOP_ORIGIN: Unit.BYTES,
    EndpointKey.L3_TOP_TARGET: Unit.BYTES,
    EndpointKey.L7_TOP_ORIGIN: Unit.REQUESTS,
    EndpointKey.L7_TOP_TARGET: Unit.REQUESTS,
    EndpointKey.L3_SUMMARY_PROTOCOL: Unit.BYTES,
    EndpointKey.L3_SUMMARY_VECTOR: Unit.BYTES,
    EndpointKey.L7_SUMMARY_HTTP_METHOD: Unit.REQUESTS,
    EndpointKey.L3_TIMESERIES: Unit.BYTES,
    EndpointKey.L7_TIMESERIES: Unit.REQUESTS,
}

_ENDPOINT_NORMALIZATION = {
    EndpointKey.L3_TOP_ATTACKS: Normalization.PERCENTAGE,
    EndpointKey.L7_TOP_ATTACKS: Normalization.PERCENTAGE,
    EndpointKey.L3_TOP_ORIGIN: Normalization.PERCENTAGE,
    EndpointKey.L3_TOP_TARGET: Normalization.PERCENTAGE,
    EndpointKey.L7_TOP_ORIGIN: Normalization.PERCENTAGE,
    EndpointKey.L7_TOP_TARGET: Normalization.PERCENTAGE,
    EndpointKey.L3_SUMMARY_PROTOCOL: Normalization.PERCENTAGE,
    EndpointKey.L3_SUMMARY_VECTOR: Normalization.PERCENTAGE,
    EndpointKey.L7_SUMMARY_HTTP_METHOD: Normalization.PERCENTAGE,
    EndpointKey.L3_TIMESERIES: Normalization.MIN0_MAX,
    EndpointKey.L7_TIMESERIES: Normalization.MIN0_MAX,
}


def adapt(
    endpoint_key: EndpointKey,
    result: object,
    *,
    refresh_id: str,
    collected_at: datetime,
) -> RadarDataset:
    """Adapt one Cloudflare endpoint result into a canonical dataset."""
    observation = build_observation(
        refresh_id=refresh_id,
        endpoint_key=endpoint_key,
        layer=_ENDPOINT_LAYER[endpoint_key],
        collected_at=collected_at,
        meta=getattr(result, "meta", None),
        default_normalization=_ENDPOINT_NORMALIZATION[endpoint_key],
        default_unit=_ENDPOINT_UNIT[endpoint_key],
    )

    if isinstance(result, CloudflareTopAttacksResult):
        pairs = adapt_attack_pairs(result, observation=observation)
        return RadarDataset(observation=observation, pairs=pairs)

    if isinstance(result, CloudflareTopLocationsResult):
        role = _role_for_endpoint(endpoint_key)
        distributions = adapt_distributions(
            result, observation=observation, role=role
        )
        return RadarDataset(
            observation=observation, distributions=distributions
        )

    if isinstance(result, CloudflareSummaryResult):
        category = _category_for_endpoint(endpoint_key)
        characteristics = adapt_characteristics(
            result, observation=observation, category=category
        )
        return RadarDataset(
            observation=observation, characteristics=characteristics
        )

    if isinstance(result, CloudflareTimeSeriesResult):
        points = adapt_timeseries(result, observation=observation)
        return RadarDataset(observation=observation, timeseries=points)

    raise TypeError(f"unsupported result type {type(result).__name__}")


def _role_for_endpoint(endpoint_key: EndpointKey) -> DistributionRole:
    if endpoint_key in {EndpointKey.L3_TOP_ORIGIN, EndpointKey.L7_TOP_ORIGIN}:
        return DistributionRole.ORIGIN
    if endpoint_key in {EndpointKey.L3_TOP_TARGET, EndpointKey.L7_TOP_TARGET}:
        return DistributionRole.TARGET
    raise ValueError(f"endpoint {endpoint_key} has no location role")


def _category_for_endpoint(endpoint_key: EndpointKey) -> CharacteristicCategory:
    if endpoint_key == EndpointKey.L3_SUMMARY_PROTOCOL:
        return CharacteristicCategory.PROTOCOL
    if endpoint_key == EndpointKey.L3_SUMMARY_VECTOR:
        return CharacteristicCategory.VECTOR
    if endpoint_key == EndpointKey.L7_SUMMARY_HTTP_METHOD:
        return CharacteristicCategory.HTTP_METHOD
    raise ValueError(f"endpoint {endpoint_key} has no characteristic category")


__all__ = [
    "adapt",
    "adapt_attack_pairs",
    "adapt_characteristics",
    "adapt_distributions",
    "adapt_timeseries",
    "build_observation",
]
