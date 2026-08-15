"""Tests for the weighted route sampler."""

from __future__ import annotations

import random
from collections import Counter
from decimal import Decimal

import pytest

from ddos_attack_project.domain.enums import Layer, Unit
from ddos_attack_project.domain.models import AttackPair
from ddos_attack_project.simulator.sampler import WeightedRouteSampler


def pair(
    source: str,
    target: str,
    share: str,
    layer: Layer = Layer.L3,
) -> AttackPair:
    return AttackPair(
        layer=layer,
        source_country_code=source,
        target_country_code=target,
        share=Decimal(share),
        unit=Unit.BYTES,
    )


def test_sample_empty_distribution() -> None:
    sampler = WeightedRouteSampler([])
    with pytest.raises(ValueError):
        sampler.sample()


def test_sample_single_item_always_returned() -> None:
    only = pair("US", "IN", "0.23")
    sampler = WeightedRouteSampler([only])
    for _ in range(50):
        assert sampler.sample(random.Random(1)) is only


def test_sample_zero_total_weight() -> None:
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0"), pair("BR", "US", "0")]
    )
    with pytest.raises(ValueError):
        sampler.sample()


def test_sample_rejects_negative_weight() -> None:
    with pytest.raises(ValueError):
        WeightedRouteSampler([pair("US", "IN", "-0.1")])


def test_sample_zero_weight_never_selected() -> None:
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0.9"), pair("BR", "US", "0")]
    )
    for _ in range(200):
        selected = sampler.sample(random.Random(3))
        assert selected.source_country_code == "US"


def test_sample_returns_complete_pair() -> None:
    # The unit of sampling is the complete edge, never origin+invented target.
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0.5"), pair("DE", "FR", "0.5")]
    )
    for _ in range(100):
        selected = sampler.sample(random.Random(5))
        assert (selected.source_country_code, selected.target_country_code) in {
            ("US", "IN"),
            ("DE", "FR"),
        }


def test_sample_statistical_frequencies() -> None:
    """Large sample should approximate the relative shares (IMPLEMENTATION 53).

    Shares are weights, not probabilities (IMPLEMENTATION 11.2). The top-N
    shares are not renormalized to sum to 1 (IMPLEMENTATION 13), so the
    expected frequency of a route among generated events is
    share / total_weight.
    """
    routes = [
        pair("US", "IN", "0.23"),
        pair("CN", "US", "0.18"),
        pair("RU", "DE", "0.12"),
        pair("BR", "US", "0.07"),
    ]
    sampler = WeightedRouteSampler(routes)
    total_weight = float(sampler.total_weight)
    samples = sampler.sample_many(20_000, rng=random.Random(42))

    counts = Counter((p.source_country_code, p.target_country_code) for p in samples)
    total = len(samples)
    tolerance = 0.02
    for route in routes:
        expected = float(route.share) / total_weight
        observed = counts[(route.source_country_code, route.target_country_code)] / total
        assert abs(observed - expected) < tolerance, (
            f"route {route.source_country_code}->{route.target_country_code} "
            f"expected {expected:.3f} got {observed:.3f}"
        )


def test_total_weight_preserves_original_shares() -> None:
    # Top-N shares are not renormalized (IMPLEMENTATION 13).
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0.23"), pair("CN", "US", "0.18")]
    )
    assert sampler.total_weight == Decimal("0.41")


def test_sample_many_negative_count() -> None:
    sampler = WeightedRouteSampler([pair("US", "IN", "1")])
    with pytest.raises(ValueError):
        sampler.sample_many(-1)
