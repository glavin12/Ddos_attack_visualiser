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


class RadarPulseCountryRef(BaseModel):
    """Country reference inside a pulse route.

    JSON shape mirrors REST ``CountryRef`` (api/schemas.py) so the frontend
    can feed pulse routes straight into the same arc-building path as REST
    routes. Shape parity is asserted by
    ``tests/test_radar_pulse_envelope.py``.
    """

    model_config = ConfigDict(extra="ignore")

    code: str
    name: str | None = None


class RadarPulseRoute(BaseModel):
    """One source→target route in a Radar pulse.

    JSON shape mirrors REST ``AttackRoute`` (api/schemas.py). ``share`` is a
    plain float (not Decimal) so ``model_dump(mode="json")`` — used by the
    WebSocket manager — emits a JSON number exactly like the REST endpoints
    do through FastAPI's encoder.
    """

    model_config = ConfigDict(extra="ignore")

    source: RadarPulseCountryRef
    target: RadarPulseCountryRef
    share: float = Field(ge=0, le=1)
    rank: int | None = None


class RadarPulseLayerData(BaseModel):
    """Pulse payload for one layer (L3 or L7).

    Freshness fields come from the layer's own latest top-attacks
    observation; ``None`` fields mean "no observation for this layer yet".
    """

    model_config = ConfigDict(extra="ignore")

    collected_at: datetime | None = None
    observation_start: datetime | None = None
    observation_end: datetime | None = None
    routes: list[RadarPulseRoute] = Field(default_factory=list)


class RadarPulseData(BaseModel):
    """The full pulse: latest 24h aggregate top routes for both layers.

    Everything here is real Cloudflare Radar data read back from the
    database — a pulse is never fabricated, and none is sent until at
    least one layer has a persisted observation.
    """

    model_config = ConfigDict(extra="ignore")

    l3: RadarPulseLayerData | None = None
    l7: RadarPulseLayerData | None = None


class ThreatIndicatorMessage(BaseModel):
    type: Literal["threat_indicator"] = "threat_indicator"
    data: ThreatIndicatorData


class StatsMessage(BaseModel):
    type: Literal["stats"] = "stats"
    data: StatsData


class SystemMessage(BaseModel):
    type: Literal["system"] = "system"
    data: SystemData


class RadarPulseMessage(BaseModel):
    type: Literal["radar_pulse"] = "radar_pulse"
    data: RadarPulseData


WebSocketMessage = Annotated[
    Union[
        ThreatIndicatorMessage,
        StatsMessage,
        SystemMessage,
        RadarPulseMessage,
    ],
    Field(discriminator="type"),
]

__all__ = [
    "RadarPulseCountryRef",
    "RadarPulseData",
    "RadarPulseLayerData",
    "RadarPulseMessage",
    "RadarPulseRoute",
    "StatsData",
    "StatsMessage",
    "SystemData",
    "SystemMessage",
    "ThreatIndicatorData",
    "ThreatIndicatorMessage",
    "WebSocketMessage",
]
