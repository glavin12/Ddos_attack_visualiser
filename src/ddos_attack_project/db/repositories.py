"""Repository for Radar observations and their normalized records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.mappers import dataset_to_rows
from ddos_attack_project.domain.enums import EndpointKey, Layer
from ddos_attack_project.domain.models import RadarDataset, ThreatIndicator


class ObservationRepository:
    """Persists and queries Radar observation datasets.

    A refresh (all 11 endpoints) is persisted as one atomic unit: either the
    entire refresh is committed or none of it is.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def save_refresh(
        self,
        datasets: list[RadarDataset],
    ) -> str:
        """Persist one refresh atomically and return its refresh_id."""
        if not datasets:
            raise ValueError("cannot save an empty refresh")

        refresh_id = datasets[0].observation.refresh_id
        if any(
            dataset.observation.refresh_id != refresh_id for dataset in datasets
        ):
            raise ValueError("all datasets in a refresh must share refresh_id")
        async with self._session_factory() as session:
            async with session.begin():
                for dataset in datasets:
                    (
                        observation_row,
                        pair_rows,
                        distribution_rows,
                        characteristic_rows,
                        timeseries_rows,
                    ) = dataset_to_rows(dataset)
                    session.add(observation_row)
                    await session.flush()
                    observation_id = observation_row.id
                    for row in (
                        *pair_rows,
                        *distribution_rows,
                        *characteristic_rows,
                        *timeseries_rows,
                    ):
                        row.observation_id = observation_id
                    session.add_all(pair_rows)
                    session.add_all(distribution_rows)
                    session.add_all(characteristic_rows)
                    session.add_all(timeseries_rows)
        return str(refresh_id)

    async def latest_observation(
        self,
        endpoint_key: EndpointKey,
        layer: Layer,
    ) -> orm.RadarObservation | None:
        """Return the most recent observation for an endpoint + layer."""
        stmt = (
            select(orm.RadarObservation)
            .where(
                orm.RadarObservation.endpoint_key == endpoint_key,
                orm.RadarObservation.layer == layer,
            )
            .order_by(orm.RadarObservation.collected_at.desc())
            .limit(1)
        )
        async with self._session_factory() as session:
            return await session.scalar(stmt)

    async def attack_pairs_for_observation(
        self,
        observation_id: str,
    ) -> list[orm.AttackPair]:
        stmt = (
            select(orm.AttackPair)
            .where(orm.AttackPair.observation_id == observation_id)
            .order_by(orm.AttackPair.share.desc())
        )
        async with self._session_factory() as session:
            return list(await session.scalars(stmt))

    async def distributions_for_observation(
        self,
        observation_id: str,
    ) -> list[orm.CountryDistribution]:
        stmt = (
            select(orm.CountryDistribution)
            .where(
                orm.CountryDistribution.observation_id == observation_id
            )
            .order_by(orm.CountryDistribution.share.desc())
        )
        async with self._session_factory() as session:
            return list(await session.scalars(stmt))

    async def characteristics_for_observation(
        self,
        observation_id: str,
    ) -> list[orm.AttackCharacteristic]:
        stmt = select(orm.AttackCharacteristic).where(
            orm.AttackCharacteristic.observation_id == observation_id
        )
        async with self._session_factory() as session:
            return list(await session.scalars(stmt))

    async def timeseries_for_observation(
        self,
        observation_id: str,
    ) -> list[orm.TimeSeriesPoint]:
        stmt = (
            select(orm.TimeSeriesPoint)
            .where(orm.TimeSeriesPoint.observation_id == observation_id)
            .order_by(orm.TimeSeriesPoint.timestamp)
        )
        async with self._session_factory() as session:
            return list(await session.scalars(stmt))

    async def latest_observation_window(
        self,
        layer: Layer,
        *,
        max_age: datetime | None = None,
    ) -> orm.RadarObservation | None:
        """Return the newest observation for a layer (any endpoint).

        If ``max_age`` is provided, only observations collected at or after
        that timestamp are considered.
        """
        stmt = (
            select(orm.RadarObservation)
            .where(orm.RadarObservation.layer == layer)
            .order_by(orm.RadarObservation.collected_at.desc())
        )
        if max_age is not None:
            stmt = stmt.where(
                orm.RadarObservation.collected_at >= max_age
            )
        stmt = stmt.limit(1)
        async with self._session_factory() as session:
            return await session.scalar(stmt)


class ThreatIndicatorRepository:
    """Persists and queries real threat indicators from public feeds.

    Uniqueness is enforced by ``(source_feed, indicator)``: a re-observed
    IOC updates ``last_seen`` (and enrichment fields) rather than inserting
    a duplicate row.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def upsert_indicators(
        self,
        indicators: Sequence[ThreatIndicator],
    ) -> tuple[int, int]:
        """Insert new indicators; refresh existing ones.

        Returns ``(inserted, updated)`` counts.
        """
        if not indicators:
            return (0, 0)

        inserted = 0
        updated = 0
        async with self._session_factory() as session:
            async with session.begin():
                for indicator in indicators:
                    stmt = select(orm.ThreatIndicator).where(
                        orm.ThreatIndicator.source_feed == indicator.source_feed,
                        orm.ThreatIndicator.indicator == indicator.indicator,
                    )
                    existing = await session.scalar(stmt)
                    if existing is None:
                        session.add(_indicator_to_row(indicator))
                        inserted += 1
                    else:
                        _apply_indicator_update(existing, indicator)
                        updated += 1
        return (inserted, updated)

    async def recent_indicators(
        self,
        *,
        limit: int = 200,
        since: datetime | None = None,
        source_feed: str | None = None,
    ) -> list[orm.ThreatIndicator]:
        """Return the most recent indicators ordered by ``last_seen`` desc."""
        stmt = select(orm.ThreatIndicator).order_by(
            orm.ThreatIndicator.last_seen.desc()
        )
        if since is not None:
            stmt = stmt.where(orm.ThreatIndicator.last_seen >= since)
        if source_feed is not None:
            stmt = stmt.where(orm.ThreatIndicator.source_feed == source_feed)
        stmt = stmt.limit(limit)
        async with self._session_factory() as session:
            return list(await session.scalars(stmt))

    async def count_active(self) -> int:
        """Count indicators actually placeable on the globe (geolocated).

        Rows without a resolved lat/lng are real IOCs too, but they're never
        rendered — see GlobeCanvas/useRadarStore. "Active on Globe" must
        match what can physically appear there, not the raw table count.
        """
        async with self._session_factory() as session:
            result = await session.scalar(
                select(func.count())
                .select_from(orm.ThreatIndicator)
                .where(orm.ThreatIndicator.latitude.is_not(None))
            )
            return result or 0

    async def prune_older_than(self, cutoff: datetime) -> int:
        """Delete indicators whose ``last_seen`` is older than ``cutoff``.

        Returns the number of deleted rows.
        """
        stmt = delete(orm.ThreatIndicator).where(
            orm.ThreatIndicator.last_seen < cutoff
        )
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(stmt)
        return int(result.rowcount or 0)


def _as_utc(dt: datetime) -> datetime:
    """Ensure a datetime is UTC-aware.

    SQLAlchemy strips tzinfo on SQLite (test dialect); Postgres preserves it.
    Comparisons need both sides in the same aware/naive world.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _indicator_to_row(indicator: ThreatIndicator) -> orm.ThreatIndicator:
    return orm.ThreatIndicator(
        source_feed=indicator.source_feed,
        indicator=indicator.indicator,
        indicator_type=indicator.indicator_type,
        resolved_ip=indicator.resolved_ip,
        country_code=indicator.country_code,
        country_name=indicator.country_name,
        city=indicator.city,
        latitude=indicator.latitude,
        longitude=indicator.longitude,
        threat_family=indicator.threat_family,
        first_seen=indicator.first_seen,
        last_seen=indicator.last_seen,
        greynoise_classification=indicator.greynoise_classification,
        greynoise_tags=indicator.greynoise_tags,
        source_url=indicator.source_url,
    )


def _apply_indicator_update(
    row: orm.ThreatIndicator,
    indicator: ThreatIndicator,
) -> None:
    """Refresh mutable fields on an existing indicator row.

    ``first_seen`` never regresses to a later time. ``last_seen`` always
    advances to the newest observation. Enrichment fields are overwritten
    when the incoming value is not None (so re-seeing an IOC never wipes
    prior enrichment).
    """
    row_first_seen = _as_utc(row.first_seen)
    row_last_seen = _as_utc(row.last_seen)
    if _as_utc(indicator.first_seen) < row_first_seen:
        row.first_seen = indicator.first_seen
    if _as_utc(indicator.last_seen) > row_last_seen:
        row.last_seen = indicator.last_seen
    if indicator.resolved_ip:
        row.resolved_ip = indicator.resolved_ip
    if indicator.country_code is not None:
        row.country_code = indicator.country_code
    if indicator.country_name is not None:
        row.country_name = indicator.country_name
    if indicator.city is not None:
        row.city = indicator.city
    if indicator.latitude is not None:
        row.latitude = indicator.latitude
    if indicator.longitude is not None:
        row.longitude = indicator.longitude
    if indicator.threat_family is not None:
        row.threat_family = indicator.threat_family
    if indicator.greynoise_classification is not None:
        row.greynoise_classification = indicator.greynoise_classification
    if indicator.greynoise_tags is not None:
        row.greynoise_tags = indicator.greynoise_tags
    if indicator.source_url is not None:
        row.source_url = indicator.source_url
