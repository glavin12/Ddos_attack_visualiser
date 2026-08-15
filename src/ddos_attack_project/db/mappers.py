"""Mappers between canonical domain objects and ORM rows."""

from __future__ import annotations

from ddos_attack_project.db import models as orm
from ddos_attack_project.domain.models import (
    AttackCharacteristic,
    AttackPair,
    DistributionEntry,
    RadarDataset,
    RadarObservation,
    TimeSeriesPoint,
)


def observation_to_row(
    observation: RadarObservation,
) -> orm.RadarObservation:
    return orm.RadarObservation(
        id=observation.id,
        refresh_id=observation.refresh_id,
        endpoint_key=observation.endpoint_key,
        layer=observation.layer,
        collected_at=observation.collected_at,
        window_start=observation.window_start,
        window_end=observation.window_end,
        cloudflare_last_updated=observation.cloudflare_last_updated,
        normalization=observation.normalization,
        unit=observation.unit,
    )


def attack_pair_to_row(
    pair: AttackPair,
    *,
    observation_id: str,
) -> orm.AttackPair:
    return orm.AttackPair(
        id=pair.id,
        observation_id=observation_id,
        layer=pair.layer,
        source_country_code=pair.source_country_code,
        source_country_name=pair.source_country_name,
        target_country_code=pair.target_country_code,
        target_country_name=pair.target_country_name,
        share=pair.share,
        rank=pair.rank,
        unit=pair.unit,
    )


def distribution_to_row(
    entry: DistributionEntry,
    *,
    observation_id: str,
) -> orm.CountryDistribution:
    return orm.CountryDistribution(
        id=entry.id,
        observation_id=observation_id,
        layer=entry.layer,
        role=entry.role,
        country_code=entry.country_code,
        country_name=entry.country_name,
        share=entry.share,
        rank=entry.rank,
        unit=entry.unit,
    )


def characteristic_to_row(
    characteristic: AttackCharacteristic,
    *,
    observation_id: str,
) -> orm.AttackCharacteristic:
    return orm.AttackCharacteristic(
        id=characteristic.id,
        observation_id=observation_id,
        layer=characteristic.layer,
        category=characteristic.category,
        value=characteristic.value,
        share=characteristic.share,
        unit=characteristic.unit,
    )


def timeseries_point_to_row(
    point: TimeSeriesPoint,
    *,
    observation_id: str,
) -> orm.TimeSeriesPoint:
    return orm.TimeSeriesPoint(
        id=point.id,
        observation_id=observation_id,
        layer=point.layer,
        timestamp=point.timestamp,
        value=point.value,
        normalization=point.normalization,
        unit=point.unit,
    )


def dataset_to_rows(
    dataset: RadarDataset,
) -> tuple[orm.RadarObservation, list[orm.AttackPair], list[orm.CountryDistribution], list[orm.AttackCharacteristic], list[orm.TimeSeriesPoint]]:
    """Convert one dataset into its ORM rows.

    Returns the observation row and the child rows. Child rows reference the
    observation by ``observation_id`` after the observation row is flushed.
    """
    observation_row = observation_to_row(dataset.observation)
    return (
        observation_row,
        [
            attack_pair_to_row(pair, observation_id=observation_row.id)
            for pair in dataset.pairs
        ],
        [
            distribution_to_row(entry, observation_id=observation_row.id)
            for entry in dataset.distributions
        ],
        [
            characteristic_to_row(
                characteristic, observation_id=observation_row.id
            )
            for characteristic in dataset.characteristics
        ],
        [
            timeseries_point_to_row(point, observation_id=observation_row.id)
            for point in dataset.timeseries
        ],
    )
