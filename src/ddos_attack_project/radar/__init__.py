"""Cloudflare Radar external API models, client, and adapters."""

from ddos_attack_project.radar.adapters import adapt
from ddos_attack_project.radar.client import (
    ENDPOINTS,
    RadarClient,
    RadarEndpoint,
    RadarError,
    RadarHTTPError,
    RadarResponseError,
)
from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareMeta,
    CloudflareSummaryResult,
    CloudflareTimeSeries,
    CloudflareTimeSeriesResult,
    CloudflareTopAttackRecord,
    CloudflareTopAttacksResult,
    CloudflareTopLocationRecord,
    CloudflareTopLocationsResult,
)

__all__ = [
    "ENDPOINTS",
    "CloudflareEnvelope",
    "CloudflareMeta",
    "CloudflareSummaryResult",
    "CloudflareTimeSeries",
    "CloudflareTimeSeriesResult",
    "CloudflareTopAttackRecord",
    "CloudflareTopAttacksResult",
    "CloudflareTopLocationRecord",
    "CloudflareTopLocationsResult",
    "RadarClient",
    "RadarEndpoint",
    "RadarError",
    "RadarHTTPError",
    "RadarResponseError",
    "adapt",
]
