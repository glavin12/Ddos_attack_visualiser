"""Tests for the synthetic event engine."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from ddos_attack_project.domain.enums import Layer, Unit
from ddos_attack_project.domain.models import AttackPair
from ddos_attack_project.simulator.engine import (
    MAX_INTENSITY,
    MIN_INTENSITY,
    SyntheticEngine,
    bounded_intensity,
)
from ddos_attack_project.simulator.geography import Geography
from ddos_attack_project.simulator.sampler import WeightedRouteSampler


def pair(source: str, target: str, share: str) -> AttackPair:
    return AttackPair(
        layer=Layer.L3,
        source_country_code=source,
        target_country_code=target,
        share=Decimal(share),
        unit=Unit.BYTES,
    )


def make_engine(**kwargs) -> SyntheticEngine:
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0.23"), pair("CN", "US", "0.18"), pair("BR", "US", "0.07")]
    )
    geography = Geography()
    return SyntheticEngine(
        sampler, geography, rng=random.Random(7), **kwargs
    )


def now() -> datetime:
    return datetime.now(UTC)


def test_bounded_intensity_range() -> None:
    assert bounded_intensity(Decimal("0"), Decimal("0.23")) == MIN_INTENSITY
    assert bounded_intensity(Decimal("0.23"), Decimal("0.23")) == MAX_INTENSITY
    for share in ("0.001", "0.05", "0.1", "0.23"):
        value = bounded_intensity(Decimal(share), Decimal("0.23"))
        assert MIN_INTENSITY <= value <= MAX_INTENSITY


def test_bounded_intensity_not_linear() -> None:
    # 23x share must not mean 23x intensity.
    low = bounded_intensity(Decimal("0.01"), Decimal("0.23"))
    high = bounded_intensity(Decimal("0.23"), Decimal("0.23"))
    ratio = high / low
    assert ratio < 23


def test_tick_fills_to_budget() -> None:
    engine = make_engine(max_active_events=50)
    spawned = engine.tick(now())
    assert len(spawned) == 50
    assert engine.active_count == 50


def test_tick_does_not_exceed_budget() -> None:
    engine = make_engine(max_active_events=5)
    engine.tick(now())
    engine.tick(now())
    assert engine.active_count == 5


def test_expire_removes_old_events() -> None:
    engine = make_engine(max_active_events=3)
    t0 = now()
    engine.tick(t0)

    expired = engine.expire(t0 + timedelta(seconds=10))
    assert len(expired) == 3
    assert engine.active_count == 0


def test_event_attribution_is_synthetic() -> None:
    engine = make_engine(max_active_events=1)
    event = engine.spawn(now())

    assert event.data.is_synthetic is True
    assert event.data.data_source == "cloudflare_radar"
    assert event.data.event_id
    assert event.data.layer == Layer.L3


def test_event_coordinates_inside_country_bounds() -> None:
    engine = make_engine(max_active_events=5)
    geography = Geography()
    for event in engine.tick(now()):
        source_geo = geography.catalog.get(event.data.source.code)
        target_geo = geography.catalog.get(event.data.target.code)
        assert source_geo.min_lat <= event.data.source.lat <= source_geo.max_lat
        assert source_geo.min_lng <= event.data.source.lon <= source_geo.max_lng
        assert target_geo.min_lat <= event.data.target.lat <= target_geo.max_lat
        assert target_geo.min_lng <= event.data.target.lon <= target_geo.max_lng


def test_event_lifetime_bounds() -> None:
    engine = make_engine(max_active_events=1, event_lifetime_seconds=4.0)
    t0 = now()
    event = engine.spawn(t0)
    assert event.created_at == t0
    assert event.expires_at - event.created_at == timedelta(seconds=4.0)


def test_update_routes_clears_pool() -> None:
    engine = make_engine(max_active_events=3)
    engine.tick(now())
    assert engine.active_count == 3

    new_sampler = WeightedRouteSampler([pair("DE", "FR", "1")])
    engine.update_routes(new_sampler)
    assert engine.active_count == 0
    spawned = engine.tick(now())
    assert len(spawned) == 3
    assert all(e.data.source.code == "DE" for e in spawned)


def test_rejects_invalid_budget() -> None:
    with pytest.raises(ValueError):
        make_engine(max_active_events=0)
