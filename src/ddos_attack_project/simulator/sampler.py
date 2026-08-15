"""Weighted route sampler for the synthetic engine.

The attack pair is the fundamental sampling unit. The engine samples a
complete source -> target edge proportional to its Radar share. It never
chooses an origin and invents a target.

Shares are used as relative weights. The top-N shares are NOT renormalized to
sum to 1; the unrepresented remainder is simply not represented in the pool
(IMPLEMENTATION 13).
"""

from __future__ import annotations

import random
from decimal import Decimal
from typing import Sequence

from ddos_attack_project.domain.models import AttackPair


class WeightedRouteSampler:
    """Samples complete attack pairs proportional to their Radar shares."""

    def __init__(self, pairs: Sequence[AttackPair]) -> None:
        self._pairs = list(pairs)
        self._weights = [pair.share for pair in self._pairs]

        for share in self._weights:
            if share < Decimal("0"):
                raise ValueError("attack pair share must be >= 0")

        self._total = sum(self._weights)

    @property
    def pairs(self) -> list[AttackPair]:
        return list(self._pairs)

    @property
    def total_weight(self) -> Decimal:
        return self._total

    def sample(self, rng: random.Random | None = None) -> AttackPair:
        """Return one complete attack pair selected by share weight."""
        if not self._pairs:
            raise ValueError("cannot sample from an empty distribution")
        if self._total <= Decimal("0"):
            raise ValueError("cannot sample from a distribution with zero total weight")

        rng = rng or random.Random()
        target = rng.random() * float(self._total)
        cumulative = 0.0
        for pair, weight in zip(self._pairs, self._weights):
            cumulative += float(weight)
            if target <= cumulative:
                return pair
        return self._pairs[-1]

    def sample_many(
        self,
        count: int,
        rng: random.Random | None = None,
    ) -> list[AttackPair]:
        """Sample ``count`` pairs; used for statistical testing."""
        if count < 0:
            raise ValueError("count must be >= 0")
        rng = rng or random.Random()
        return [self.sample(rng) for _ in range(count)]
