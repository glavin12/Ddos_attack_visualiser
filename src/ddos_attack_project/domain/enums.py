"""Enumerations used across the canonical domain layer."""

from __future__ import annotations

from enum import StrEnum


class Layer(StrEnum):
    """Attack layer identifiers returned by Cloudflare Radar."""

    L3 = "L3"
    L7 = "L7"


class Unit(StrEnum):
    """Units preserved from Cloudflare Radar responses."""

    BYTES = "bytes"
    REQUESTS = "requests"


class Normalization(StrEnum):
    """Normalization applied by Cloudflare Radar to a value."""

    PERCENTAGE = "PERCENTAGE"
    MIN0_MAX = "MIN0_MAX"


class DistributionRole(StrEnum):
    """Role of a country within an observation dataset."""

    ORIGIN = "origin"
    TARGET = "target"


class CharacteristicCategory(StrEnum):
    """Categories available in attack-characteristics datasets."""

    PROTOCOL = "protocol"
    VECTOR = "vector"
    HTTP_METHOD = "http_method"


class EndpointKey(StrEnum):
    """Stable identifiers for each configured Radar endpoint.

    The values match the keys used to store captured sample responses.
    """

    L3_TOP_ATTACKS = "layer3-top-attacks"
    L7_TOP_ATTACKS = "layer7-top-attacks"
    L3_TOP_ORIGIN = "layer3-top-origin"
    L3_TOP_TARGET = "layer3-top-target"
    L7_TOP_ORIGIN = "layer7-top-origin"
    L7_TOP_TARGET = "layer7-top-target"
    L3_SUMMARY_PROTOCOL = "layer3-summary-protocol"
    L3_SUMMARY_VECTOR = "layer3-summary-vector"
    L7_SUMMARY_HTTP_METHOD = "layer7-summary-http-method"
    L3_TIMESERIES = "layer3-timeseries"
    L7_TIMESERIES = "layer7-timeseries"
