"""WebSocket message envelope models.

All messages use a common envelope: ``{ "type": ..., "data": ... }``.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from ddos_attack_project.domain.enums import Layer


class SourceTarget(BaseModel):
    code: str
    name: str | None = None
    lat: float
    lon: float


class AttackEventData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: str
    layer: Layer
    source: SourceTarget
    target: SourceTarget
    intensity: float = Field(ge=0.0, le=1.0)
    is_synthetic: bool = True
    data_source: Literal["cloudflare_radar", "synthetic"] = "cloudflare_radar"


class StatsData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    active_events: int = Field(ge=0)


class SystemData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


class AttackEventMessage(BaseModel):
    type: Literal["attack_event"] = "attack_event"
    data: AttackEventData


class StatsMessage(BaseModel):
    type: Literal["stats"] = "stats"
    data: StatsData


class SystemMessage(BaseModel):
    type: Literal["system"] = "system"
    data: SystemData


WebSocketMessage = Annotated[
    Union[AttackEventMessage, StatsMessage, SystemMessage],
    Field(discriminator="type"),
]

__all__ = [
    "AttackEventData",
    "AttackEventMessage",
    "SourceTarget",
    "StatsData",
    "StatsMessage",
    "SystemData",
    "SystemMessage",
    "WebSocketMessage",
]
