"""REST API response models.

These define the normalized application contracts the frontend consumes.
The frontend never receives Cloudflare's raw JSON format.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    Layer,
    Normalization,
    Unit,
)


class ObservationMeta(BaseModel):
    """Current observation window and freshness metadata."""

    start: datetime | None = None
    end: datetime | None = None
    last_updated: datetime | None = None
    collected_at: datetime | None = None


class CountryRef(BaseModel):
    code: str
    name: str | None = None


class AttackRoute(BaseModel):
    source: CountryRef
    target: CountryRef
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rank: int | None = None


class CountryRank(BaseModel):
    country: CountryRef
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    rank: int | None = None


class CharacteristicValue(BaseModel):
    value: str
    share: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))


class HistoryPoint(BaseModel):
    timestamp: datetime
    value: float


class OverviewResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    observation: ObservationMeta
    layer: Layer
    top_routes: list[AttackRoute] = Field(default_factory=list)
    top_origins: list[CountryRank] = Field(default_factory=list)
    top_targets: list[CountryRank] = Field(default_factory=list)


class AttacksResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    layer: Layer
    unit: Unit
    entries: list[AttackRoute] = Field(default_factory=list)


class CountriesResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    layer: Layer
    role: DistributionRole
    unit: Unit
    entries: list[CountryRank] = Field(default_factory=list)


class CharacteristicsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    layer: Layer
    type: CharacteristicCategory
    unit: Unit
    entries: list[CharacteristicValue] = Field(default_factory=list)


class HistoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    layer: Layer
    unit: Unit
    normalization: Normalization
    aggregation: str
    points: list[HistoryPoint] = Field(default_factory=list)


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str
    observation_start: datetime | None = None
    observation_end: datetime | None = None
    last_updated: datetime | None = None
    collected_at: datetime | None = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "ok"
