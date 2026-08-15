"""Synthetic attack events and the active-event engine.

Synthetic events are temporary visual objects driven by the real Radar
distribution. The underlying distribution is real; the visual realization is
synthetic. Events are never persisted to PostgreSQL.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ddos_attack_project.domain.enums import Layer
from ddos_attack_project.simulator.geography import Geography
from ddos_attack_project.simulator.sampler import WeightedRouteSampler
from ddos_attack_project.websocket.envelopes import (
    AttackEventData,
    SourceTarget,
)

#: Bounded visual intensity range (IMPLEMENTATION 19).
MIN_INTENSITY: float = 0.3
MAX_INTENSITY: float = 1.0


def bounded_intensity(share: Decimal, max_share: Decimal) -> float:
    """Map a share into the bounded intensity range [0.3, 1.0].

    The mapping is deliberately not linear: a route with 23x the share must
    not appear 23x brighter. A sqrt curve keeps balance while still letting
    higher-share routes appear stronger.
    """
    if max_share <= Decimal("0"):
        return MIN_INTENSITY
    normalized = float(share / max_share)
    if normalized <= 0:
        return MIN_INTENSITY
    return MIN_INTENSITY + (MAX_INTENSITY - MIN_INTENSITY) * min(1.0, normalized**0.5)


@dataclass(frozen=True)
class SyntheticEvent:
    """A temporary visualization event plus its lifetime."""

    data: AttackEventData
    created_at: datetime
    expires_at: datetime

    @property
    def event_id(self) -> str:
        return self.data.event_id


class SyntheticEngine:
    """Maintains the bounded active-event pool.

    The engine continuously recycles events: expired events are removed and
    new events are spawned from the weighted route sampler until the budget
    is full.
    """

    def __init__(
        self,
        sampler: WeightedRouteSampler,
        geography: Geography,
        *,
        max_active_events: int = 50,
        event_lifetime_seconds: float = 4.0,
        rng: random.Random | None = None,
    ) -> None:
        if max_active_events < 1:
            raise ValueError("max_active_events must be >= 1")
        self._sampler = sampler
        self._geography = geography
        self._max_active = max_active_events
        self._lifetime = timedelta(seconds=event_lifetime_seconds)
        self._rng = rng or random.Random()
        self._active: list[SyntheticEvent] = []

    @property
    def active_events(self) -> list[SyntheticEvent]:
        return list(self._active)

    @property
    def active_count(self) -> int:
        return len(self._active)

    def expire(self, now: datetime) -> list[SyntheticEvent]:
        """Remove expired events and return them."""
        expired = [event for event in self._active if event.expires_at <= now]
        self._active = [event for event in self._active if event.expires_at > now]
        return expired

    def spawn(self, now: datetime) -> SyntheticEvent:
        """Create one synthetic event from the weighted route sampler."""
        pair = self._sampler.sample(self._rng)
        max_share = max((p.share for p in self._sampler.pairs), default=Decimal("0"))

        source_point = self._geography.random_point(pair.source_country_code, rng=self._rng)
        target_point = self._geography.random_point(pair.target_country_code, rng=self._rng)

        event = SyntheticEvent(
            data=AttackEventData(
                event_id=str(uuid.uuid4()),
                layer=Layer(pair.layer.value),
                source=SourceTarget(
                    code=pair.source_country_code,
                    name=pair.source_country_name,
                    lat=source_point.lat,
                    lon=source_point.lng,
                ),
                target=SourceTarget(
                    code=pair.target_country_code,
                    name=pair.target_country_name,
                    lat=target_point.lat,
                    lon=target_point.lng,
                ),
                intensity=bounded_intensity(pair.share, max_share),
                is_synthetic=True,
                data_source="cloudflare_radar",
            ),
            created_at=now,
            expires_at=now + self._lifetime,
        )
        self._active.append(event)
        return event

    def tick(self, now: datetime) -> list[SyntheticEvent]:
        """Expire stale events, then top the pool back up to the budget.

        Returns the newly spawned events.
        """
        self.expire(now)
        spawned: list[SyntheticEvent] = []
        while self.active_count < self._max_active:
            spawned.append(self.spawn(now))
        return spawned

    def update_routes(self, sampler: WeightedRouteSampler) -> None:
        """Swap in a new route distribution without losing the pool."""
        self._sampler = sampler
        self._active.clear()
