"""Tests for SQLAlchemy ORM model definitions."""

from __future__ import annotations

from ddos_attack_project.db.models import (
    AttackCharacteristic,
    AttackPair,
    Base,
    CountryDistribution,
    RadarObservation,
    TimeSeriesPoint,
)


def test_expected_tables_registered() -> None:
    tables = set(Base.metadata.tables)
    assert {
        "radar_observations",
        "attack_pairs",
        "country_distributions",
        "attack_characteristics",
        "timeseries_points",
    } <= tables


def test_attack_pair_columns() -> None:
    columns = AttackPair.__table__.columns
    assert set(columns.keys()) >= {
        "id",
        "observation_id",
        "layer",
        "source_country_code",
        "source_country_name",
        "target_country_code",
        "target_country_name",
        "share",
        "rank",
        "unit",
    }


def test_observation_columns() -> None:
    columns = RadarObservation.__table__.columns
    assert set(columns.keys()) >= {
        "id",
        "refresh_id",
        "endpoint_key",
        "layer",
        "collected_at",
        "window_start",
        "window_end",
        "cloudflare_last_updated",
        "normalization",
        "unit",
    }


def test_distribution_columns() -> None:
    columns = CountryDistribution.__table__.columns
    assert set(columns.keys()) >= {
        "id",
        "observation_id",
        "layer",
        "role",
        "country_code",
        "country_name",
        "share",
        "rank",
        "unit",
    }


def test_characteristic_columns() -> None:
    columns = AttackCharacteristic.__table__.columns
    assert set(columns.keys()) >= {
        "id",
        "observation_id",
        "layer",
        "category",
        "value",
        "share",
        "unit",
    }


def test_timeseries_columns() -> None:
    columns = TimeSeriesPoint.__table__.columns
    assert set(columns.keys()) >= {
        "id",
        "observation_id",
        "layer",
        "timestamp",
        "value",
        "normalization",
        "unit",
    }
