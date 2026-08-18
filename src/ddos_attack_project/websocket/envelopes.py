"""WebSocket message envelope models.

All messages use a common envelope: ``{ "type": ..., "data": ... }``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from ddos_attack_project.domain.enums import IndicatorType, SourceFeed
from ddos_attack_project.domain.models import ThreatIndicator


class ThreatIndicatorData(BaseModel):
    """A real threat indicator broadcast to the frontend.

    Every field is real: the source feed and IOC come from public feeds,
    coordinates come from MaxMind GeoLite2 (or are null when unknown),
    and timestamps are the feed's own observation times.
    """

    model_config = ConfigDict(extra="ignore")

    indicator: str
    indicator_type: IndicatorType
    source_feed: SourceFeed
    resolved_ip: str
    country_code: str | None = None
    country_name: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    threat_family: str | None = None
    first_seen: datetime
    last_seen: datetime
    greynoise_classification: str | None = None
    greynoise_tags: str | None = None
    source_url: str | None = None

    @classmethod
    def from_domain(cls, indicator: ThreatIndicator) -> "ThreatIndicatorData":
        return cls(
            indicator=indicator.indicator,
            indicator_type=indicator.indicator_type,
            source_feed=indicator.source_feed,
            resolved_ip=indicator.resolved_ip,
            country_code=indicator.country_code,
            country_name=indicator.country_name,
            city=indicator.city,
            lat=indicator.latitude,
            lng=indicator.longitude,
            threat_family=indicator.threat_family,
            first_seen=indicator.first_seen,
            last_seen=indicator.last_seen,
            greynoise_classification=indicator.greynoise_classification,
            greynoise_tags=indicator.greynoise_tags,
            source_url=indicator.source_url,
        )


class StatsData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    active_indicators: int = Field(default=0, ge=0)


class SystemData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


class ThreatIndicatorMessage(BaseModel):
    type: Literal["threat_indicator"] = "threat_indicator"
    data: ThreatIndicatorData


class StatsMessage(BaseModel):
    type: Literal["stats"] = "stats"
    data: StatsData


class SystemMessage(BaseModel):
    type: Literal["system"] = "system"
    data: SystemData


WebSocketMessage = Annotated[
    Union[ThreatIndicatorMessage, StatsMessage, SystemMessage],
    Field(discriminator="type"),
]

__all__ = [
    "StatsData",
    "StatsMessage",
    "SystemData",
    "SystemMessage",
    "ThreatIndicatorData",
    "ThreatIndicatorMessage",
    "WebSocketMessage",
]
