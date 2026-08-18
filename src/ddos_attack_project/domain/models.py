"""Canonical normalized domain models.

These are the internal language of the application. They intentionally do
not mirror Cloudflare's raw JSON field names (see ``radar.external``).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    IndicatorType,
    Layer,
    Normalization,
    SourceFeed,
    Unit,
)

COUNTRY_CODE_PATTERN = r"^[A-Z0-9]{2}$"


class Country(BaseModel):
    """A country referenced by an observation."""

    code: str = Field(pattern=COUNTRY_CODE_PATTERN)
    name: str | None = None


class RadarObservation(BaseModel):
    """Metadata identifying one collected Radar endpoint response.

    A refresh creates one ``RadarObservation`` per endpoint response, all
    sharing the same ``refresh_id``.
    """

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    refresh_id: uuid.UUID
    endpoint_key: EndpointKey
    layer: Layer
    collected_at: datetime
    window_start: datetime | None = None
    window_end: datetime | None = None
    cloudflare_last_updated: datetime | None = None
    normalization: Normalization
    unit: Unit


class AttackPair(BaseModel):
    """A source-country to target-country relationship from ``top/attacks``."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    observation_id: uuid.UUID | None = None
    layer: Layer
    source_country_code: str = Field(pattern=COUNTRY_CODE_PATTERN)
    source_country_name: str | None = None
    target_country_code: str = Field(pattern=COUNTRY_CODE_PATTERN)
    target_country_name: str | None = None
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rank: int | None = Field(default=None, ge=1)
    unit: Unit


class DistributionEntry(BaseModel):
    """A country-level origin or target distribution record."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    observation_id: uuid.UUID | None = None
    layer: Layer
    role: DistributionRole
    country_code: str = Field(pattern=COUNTRY_CODE_PATTERN)
    country_name: str | None = None
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rank: int | None = Field(default=None, ge=1)
    unit: Unit


class AttackCharacteristic(BaseModel):
    """An attack-characteristic share (protocol, vector, HTTP method)."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    observation_id: uuid.UUID | None = None
    layer: Layer
    category: CharacteristicCategory
    value: str
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    unit: Unit


class TimeSeriesPoint(BaseModel):
    """A single relative-activity point from a timeseries response."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    observation_id: uuid.UUID | None = None
    layer: Layer
    timestamp: datetime
    value: float
    normalization: Normalization = Normalization.MIN0_MAX
    unit: Unit

    @field_validator("value")
    @classmethod
    def _check_value_in_range(cls, value: float) -> float:
        if value < 0.0 or value > 1.0:
            raise ValueError("timeseries value must be within [0, 1]")
        return value


class ThreatIndicator(BaseModel):
    """A real IOC observed by a public threat-intel feed.

    ``resolved_ip`` is always populated: for IP indicators it equals
    ``indicator``; for URL/domain indicators it is the numeric IP the
    ingestor resolved and geolocated. Every geolocation field is optional
    so honest "unknown location" cases are representable.
    """

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    source_feed: SourceFeed
    indicator: str
    indicator_type: IndicatorType
    resolved_ip: str
    country_code: str | None = Field(default=None, pattern=COUNTRY_CODE_PATTERN)
    country_name: str | None = None
    city: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    threat_family: str | None = None
    first_seen: datetime
    last_seen: datetime
    greynoise_classification: str | None = None
    greynoise_tags: str | None = None
    source_url: str | None = None


class RadarDataset(BaseModel):
    """One normalized endpoint response: an observation plus its records.

    Adapters produce these; ingestion persists them. Exactly one of the
    record lists is populated for any given endpoint.
    """

    observation: RadarObservation
    pairs: list[AttackPair] = Field(default_factory=list)
    distributions: list[DistributionEntry] = Field(default_factory=list)
    characteristics: list[AttackCharacteristic] = Field(default_factory=list)
    timeseries: list[TimeSeriesPoint] = Field(default_factory=list)
