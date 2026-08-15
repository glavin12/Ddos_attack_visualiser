"""Tests for the async event scheduler."""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta

import pytest

from ddos_attack_project.simulator.engine import SyntheticEngine
from ddos_attack_project.simulator.geography import Geography
from ddos_attack_project.simulator.sampler import WeightedRouteSampler
from ddos_attack_project.simulator.scheduler import EventScheduler

from tests.test_engine import pair


class _FakeClock:
    def __init__(self) -> None:
        self._now = datetime.now(UTC)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


def make_engine(max_active_events: int = 5) -> SyntheticEngine:
    sampler = WeightedRouteSampler(
        [pair("US", "IN", "0.5"), pair("CN", "US", "0.5")]
    )
    return SyntheticEngine(
        sampler,
        Geography(),
        max_active_events=max_active_events,
        rng=random.Random(3),
    )


async def test_scheduler_broadcasts_and_stops() -> None:
    engine = make_engine(max_active_events=3)
    scheduler = EventScheduler(engine, interval_seconds=0.001)
    stop = asyncio.Event()
    broadcasted: list = []

    async def broadcast(event) -> None:
        broadcasted.append(event)
        if len(broadcasted) >= 6:
            stop.set()

    await scheduler.run(broadcast, stop=stop)
    assert len(broadcasted) >= 6
    assert all(e.data.is_synthetic for e in broadcasted)


async def test_scheduler_second_tick_broadcasts_nothing_until_expiry() -> None:
    engine = make_engine(max_active_events=3)
    scheduler = EventScheduler(engine, interval_seconds=0.001)
    stop = asyncio.Event()
    first_batch: list = []

    async def broadcast(event) -> None:
        if len(first_batch) < 3:
            first_batch.append(event)
            if len(first_batch) == 3:
                stop.set()

    await scheduler.run(broadcast, stop=stop)
    assert len(first_batch) == 3
    assert engine.active_count == 3


async def test_scheduler_rejects_concurrent_run() -> None:
    engine = make_engine(max_active_events=1)
    scheduler = EventScheduler(engine, interval_seconds=0.001)
    stop = asyncio.Event()

    async def broadcast(event) -> None:
        stop.set()

    first = asyncio.create_task(scheduler.run(broadcast, stop=stop))
    await asyncio.sleep(0.01)
    with pytest.raises(RuntimeError):
        await scheduler.run(broadcast, stop=stop)
    first.cancel()
    await asyncio.gather(first, return_exceptions=True)


async def test_scheduler_is_reusable_after_stop() -> None:
    engine = make_engine(max_active_events=1)
    clock = _FakeClock()
    scheduler = EventScheduler(engine, interval_seconds=0.001, clock=clock)
    stop = asyncio.Event()
    total: list = []

    async def broadcast(event) -> None:
        total.append(event)
        stop.set()

    await scheduler.run(broadcast, stop=stop)
    assert len(total) == 1

    # Advance past the event lifetime so the pool empties on the next tick.
    clock.advance(seconds=10)
    stop.clear()
    await scheduler.run(broadcast, stop=stop)
    assert len(total) == 2
