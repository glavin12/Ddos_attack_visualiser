"""Repository for Radar observations and their normalized records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.mappers import dataset_to_rows
from ddos_attack_project.domain.enums import EndpointKey, Layer
from ddos_attack_project.domain.models import RadarDataset


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
