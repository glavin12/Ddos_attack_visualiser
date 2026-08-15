"""REST API routes for the normalized Radar data."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from ddos_attack_project.api.schemas import (
    AttacksResponse,
    CharacteristicsResponse,
    CountriesResponse,
    HealthResponse,
    HistoryResponse,
    OverviewResponse,
    StatusResponse,
)
from ddos_attack_project.api.service import RadarQueryService
from ddos_attack_project.dependencies import get_radar_service
from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    Layer,
)

router = APIRouter(prefix="/api/v1")


ServiceDep = Annotated[RadarQueryService, Depends(get_radar_service)]

LayerQuery = Annotated[Layer, Query(description="Attack layer: L3 or L7")]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Deployment health",
)
async def get_health(service: ServiceDep) -> HealthResponse:
    return await service.health()


@router.get(
    "/radar/status",
    response_model=StatusResponse,
    summary="Current dataset status",
)
async def get_radar_status(service: ServiceDep) -> StatusResponse:
    return await service.status()


@router.get(
    "/radar/overview",
    response_model=OverviewResponse,
    summary="Initial dashboard state",
)
async def get_radar_overview(
    service: ServiceDep,
    layer: LayerQuery,
) -> OverviewResponse:
    return await service.overview(layer)


@router.get(
    "/radar/attacks",
    response_model=AttacksResponse,
    summary="Normalized source-to-target attack pairs",
)
async def get_radar_attacks(
    service: ServiceDep,
    layer: LayerQuery,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> AttacksResponse:
    return await service.attacks(layer, limit=limit)


@router.get(
    "/radar/countries",
    response_model=CountriesResponse,
    summary="Top origin or target country rankings",
)
async def get_radar_countries(
    service: ServiceDep,
    layer: LayerQuery,
    role: Annotated[
        DistributionRole, Query(description="origin or target")
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> CountriesResponse:
    return await service.countries(layer, role, limit=limit)


@router.get(
    "/radar/characteristics",
    response_model=CharacteristicsResponse,
    summary="Protocol, vector, or HTTP method distribution",
)
async def get_radar_characteristics(
    service: ServiceDep,
    layer: LayerQuery,
    type: Annotated[
        CharacteristicCategory,
        Query(description="protocol, vector, or http_method"),
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> CharacteristicsResponse:
    return await service.characteristics(layer, type, limit=limit)


@router.get(
    "/radar/history",
    response_model=HistoryResponse,
    summary="Seven-day relative activity history",
)
async def get_radar_history(
    service: ServiceDep,
    layer: LayerQuery,
    limit: Annotated[int, Query(ge=1, le=2000)] = 200,
) -> HistoryResponse:
    return await service.history(layer, limit=limit)
