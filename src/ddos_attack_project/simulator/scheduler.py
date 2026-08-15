"""Async scheduler that drives the synthetic engine and broadcasts events."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Protocol

from ddos_attack_project.simulator.engine import SyntheticEngine, SyntheticEvent

Broadcast = Callable[[SyntheticEvent], Awaitable[None]]


class Clock(Protocol):
    def __call__(self) -> datetime: ...


class EventScheduler:
    """Runs the engine loop: expire, spawn to budget, broadcast new events."""

    def __init__(
        self,
        engine: SyntheticEngine,
        *,
        interval_seconds: float = 0.25,
        clock: Clock | None = None,
    ) -> None:
        self._engine = engine
        self._interval = interval_seconds
        self._clock = clock or (lambda: datetime.now(UTC))
        self._running = False

    @property
    def engine(self) -> SyntheticEngine:
        return self._engine

    async def run(
        self,
        broadcast: Broadcast,
        *,
        stop: asyncio.Event | None = None,
    ) -> None:
        """Run until ``stop`` is set (or forever)."""
        if self._running:
            raise RuntimeError("scheduler is already running")
        self._running = True
        try:
            while True:
                if stop is not None and stop.is_set():
                    break
                now = self._clock()
                spawned = self._engine.tick(now)
                for event in spawned:
                    await broadcast(event)
                await asyncio.sleep(self._interval)
        finally:
            self._running = False
