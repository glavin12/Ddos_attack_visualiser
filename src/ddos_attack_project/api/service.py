"""Query service mapping normalized database rows to API responses.

The frontend consumes these responses and never sees Cloudflare's raw JSON.

Error signals are deliberately narrow:
- "no data yet" → 200 OK with empty entries + a null observation.collected_at.
- real backend errors (DB down, corrupt row) → SQLAlchemyError propagates out
  and the FastAPI exception handler in ``main`` turns it into HTTP 503.

The distinction lets the frontend render "still warming up" and "something
is broken" differently instead of guessing from an empty response.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ddos_attack_project.api.schemas import (
    AttacksResponse,
    AttackRoute,
    CharacteristicsResponse,
    CharacteristicValue,
    CountriesResponse,
    CountryRank,
    CountryRef,
    HealthResponse,
    HistoryPoint,
    HistoryResponse,
    ObservationMeta,
    OverviewResponse,
    StatusResponse,
)
from ddos_attack_project.db import models as orm
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    DistributionRole,
    EndpointKey,
    Layer,
    Normalization,
    Unit,
)

_ENDPOINT_ATTACKS = {
    Layer.L3: EndpointKey.L3_TOP_ATTACKS,
    Layer.L7: EndpointKey.L7_TOP_ATTACKS,
}
_ENDPOINT_ORIGIN = {
    Layer.L3: EndpointKey.L3_TOP_ORIGIN,
    Layer.L7: EndpointKey.L7_TOP_ORIGIN,
}
_ENDPOINT_TARGET = {
    Layer.L3: EndpointKey.L3_TOP_TARGET,
    Layer.L7: EndpointKey.L7_TOP_TARGET,
}
_ENDPOINT_CHARACTERISTICS = {
    (Layer.L3, CharacteristicCategory.PROTOCOL): EndpointKey.L3_SUMMARY_PROTOCOL,
    (Layer.L3, CharacteristicCategory.VECTOR): EndpointKey.L3_SUMMARY_VECTOR,
    (Layer.L7, CharacteristicCategory.HTTP_METHOD): EndpointKey.L7_SUMMARY_HTTP_METHOD,
}
_ENDPOINT_TIMESERIES = {
    Layer.L3: EndpointKey.L3_TIMESERIES,
    Layer.L7: EndpointKey.L7_TIMESERIES,
}


class RadarQueryService:
    """Reads the latest normalized observations and builds API responses."""

    def __init__(
        self,
        repository: ObservationRepository,
        *,
        stale_after_seconds: int = 3600,
    ) -> None:
        self._repository = repository
        self._stale_after = timedelta(seconds=stale_after_seconds)

    async def overview(self, layer: Layer) -> OverviewResponse:
        attacks_obs = await self._repository.latest_observation(
            _ENDPOINT_ATTACKS[layer], layer
        )
        origin_obs = await self._repository.latest_observation(
            _ENDPOINT_ORIGIN[layer], layer
        )
        target_obs = await self._repository.latest_observation(
            _ENDPOINT_TARGET[layer], layer
        )

        meta = _observation_meta(attacks_obs)
        top_routes: list[AttackRoute] = []
        top_origins: list[CountryRank] = []
        top_targets: list[CountryRank] = []

        if attacks_obs is not None:
            pairs = await self._repository.attack_pairs_for_observation(
                attacks_obs.id
            )
            top_routes = [_attack_route(row) for row in pairs[:100]]

        if origin_obs is not None:
            origins = await self._repository.distributions_for_observation(
                origin_obs.id
            )
            top_origins = [_country_rank(row) for row in origins[:50]]

        if target_obs is not None:
            targets = await self._repository.distributions_for_observation(
                target_obs.id
            )
            top_targets = [_country_rank(row) for row in targets[:50]]

        return OverviewResponse(
            observation=meta,
            layer=layer,
            top_routes=top_routes,
            top_origins=top_origins,
            top_targets=top_targets,
        )

    async def attacks(
        self,
        layer: Layer,
        *,
        limit: int = 100,
    ) -> AttacksResponse:
        observation = await self._repository.latest_observation(
            _ENDPOINT_ATTACKS[layer], layer
        )
        if observation is None:
            return AttacksResponse(layer=layer, unit=_unit(layer), entries=[])
        pairs = await self._repository.attack_pairs_for_observation(
            observation.id
        )
        return AttacksResponse(
            layer=layer,
            unit=Unit(observation.unit),
            entries=[_attack_route(row) for row in pairs[:limit]],
        )

    async def countries(
        self,
        layer: Layer,
        role: DistributionRole,
        *,
        limit: int = 50,
    ) -> CountriesResponse:
        endpoint_key = (
            _ENDPOINT_ORIGIN[layer]
            if role == DistributionRole.ORIGIN
            else _ENDPOINT_TARGET[layer]
        )
        observation = await self._repository.latest_observation(
            endpoint_key, layer
        )
        if observation is None:
            return CountriesResponse(
                layer=layer, role=role, unit=_unit(layer), entries=[]
            )
        entries = await self._repository.distributions_for_observation(
            observation.id
        )
        return CountriesResponse(
            layer=layer,
            role=role,
            unit=Unit(observation.unit),
            entries=[_country_rank(row) for row in entries[:limit]],
        )

    async def characteristics(
        self,
        layer: Layer,
        category: CharacteristicCategory,
        *,
        limit: int = 50,
    ) -> CharacteristicsResponse:
        endpoint_key = _ENDPOINT_CHARACTERISTICS.get((layer, category))
        if endpoint_key is None:
            return CharacteristicsResponse(
                layer=layer, type=category, unit=_unit(layer), entries=[]
            )
        observation = await self._repository.latest_observation(
            endpoint_key, layer
        )
        if observation is None:
            return CharacteristicsResponse(
                layer=layer, type=category, unit=_unit(layer), entries=[]
            )
        rows = await self._repository.characteristics_for_observation(
            observation.id
        )
        return CharacteristicsResponse(
            layer=layer,
            type=category,
            unit=Unit(observation.unit),
            entries=[
                CharacteristicValue(value=row.value, share=row.share)
                for row in rows[:limit]
            ],
        )

    async def history(
        self,
        layer: Layer,
        *,
        limit: int = 200,
    ) -> HistoryResponse:
        observation = await self._repository.latest_observation(
            _ENDPOINT_TIMESERIES[layer], layer
        )
        if observation is None:
            return HistoryResponse(
                layer=layer,
                unit=_unit(layer),
                normalization=Normalization.MIN0_MAX,
                aggregation="ONE_HOUR",
                points=[],
            )
        rows = await self._repository.timeseries_for_observation(observation.id)
        return HistoryResponse(
            layer=layer,
            unit=Unit(observation.unit),
            normalization=Normalization(observation.normalization),
            aggregation="ONE_HOUR",
            points=[
                HistoryPoint(timestamp=row.timestamp, value=row.value)
                for row in rows[:limit]
            ],
        )

    async def status(self) -> StatusResponse:
        """Report dataset freshness for the most recent observations."""
        recent: orm.RadarObservation | None = None
        for layer in (Layer.L3, Layer.L7):
            observation = await self._repository.latest_observation_window(
                layer, max_age=datetime.now(UTC) - self._stale_after
            )
            if observation is not None and (
                recent is None
                or observation.collected_at > recent.collected_at
            ):
                recent = observation

        if recent is None:
            return StatusResponse(status="degraded")

        return StatusResponse(
            status="healthy",
            observation_start=recent.window_start,
            observation_end=recent.window_end,
            last_updated=recent.cloudflare_last_updated,
            collected_at=recent.collected_at,
        )

    async def health(self) -> HealthResponse:
        """Return deployment health (kept intentionally boring)."""
        return HealthResponse(status="ok")


def _unit(layer: Layer) -> Unit:
    return Unit.BYTES if layer == Layer.L3 else Unit.REQUESTS


def _observation_meta(
    observation: orm.RadarObservation | None,
) -> ObservationMeta:
    if observation is None:
        return ObservationMeta()
    return ObservationMeta(
        start=observation.window_start,
        end=observation.window_end,
        last_updated=observation.cloudflare_last_updated,
        collected_at=observation.collected_at,
    )


def _country_ref(code: str, name: str | None) -> CountryRef:
    return CountryRef(code=code, name=name)


def _attack_route(row: orm.AttackPair) -> AttackRoute:
    return AttackRoute(
        source=_country_ref(row.source_country_code, row.source_country_name),
        target=_country_ref(row.target_country_code, row.target_country_name),
        share=row.share,
        rank=row.rank,
    )


def _country_rank(row: orm.CountryDistribution) -> CountryRank:
    return CountryRank(
        country=_country_ref(row.country_code, row.country_name),
        share=row.share,
        rank=row.rank,
    )
