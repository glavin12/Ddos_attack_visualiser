"""Simulation runtime: wires the repository to the synthetic engine.

Loads the latest real attack pairs from the database, builds a weighted
sampler, and runs the scheduler, broadcasting synthetic visualization events
and periodic stats through the WebSocket connection manager.
"""

from __future__ import annotations

import asyncio
import logging

from ddos_attack_project.api.service import _ENDPOINT_ATTACKS
from ddos_attack_project.config import AppSettings
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import Layer, Unit
from ddos_attack_project.domain.models import AttackPair
from ddos_attack_project.simulator.engine import SyntheticEngine
from ddos_attack_project.simulator.geography import Geography
from ddos_attack_project.simulator.sampler import WeightedRouteSampler
from ddos_attack_project.simulator.scheduler import EventScheduler
from ddos_attack_project.websocket.envelopes import AttackEventMessage
from ddos_attack_project.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)


class SimulationRuntime:
    """Owns the synthetic engine lifecycle for the application."""

    def __init__(
        self,
        repository: ObservationRepository,
        manager: ConnectionManager,
        settings: AppSettings,
        *,
        geography: Geography | None = None,
    ) -> None:
        self._repository = repository
        self._manager = manager
        self._settings = settings
        self._geography = geography or Geography()
        self._engine: SyntheticEngine | None = None
        self._scheduler: EventScheduler | None = None
        self._stop: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    @property
    def active_events(self) -> int:
        return self._engine.active_count if self._engine is not None else 0

    async def start(self) -> None:
        """Load routes, build the engine, and start the scheduler task."""
        try:
            pairs = await self._load_pairs()
        except Exception as exc:
            logger.warning(
                "Failed to load initial attack routes from database: %s", exc
            )
            pairs = []

        if not pairs:
            await self._manager.broadcast_system(
                "No Radar data available yet"
            )
            return

        sampler = WeightedRouteSampler(pairs)
        engine = SyntheticEngine(
            sampler,
            self._geography,
            max_active_events=self._settings.max_active_events,
            event_lifetime_seconds=self._settings.event_lifetime_ms / 1000.0,
        )
        scheduler = EventScheduler(
            engine,
            interval_seconds=self._settings.ws_event_interval_ms / 1000.0,
        )
        self._engine = engine
        self._scheduler = scheduler
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self._run(scheduler))
        await self._manager.broadcast_system("Simulation started")
        logger.info("simulation started with %d routes", len(pairs))

    async def stop(self) -> None:
        """Stop the scheduler task and cancel the stats loop."""
        if self._stop is not None:
            self._stop.set()
        if self._task is not None:
            await asyncio.wait([self._task])

    async def _run(self, scheduler: EventScheduler) -> None:
        stats_interval = self._settings.ws_stats_interval_ms / 1000.0

        async def stats_loop() -> None:
            while not self._stop.is_set():
                await self._manager.broadcast_stats(self.active_events)
                await asyncio.sleep(stats_interval)

        async def broadcast(event) -> None:
            await self._manager.broadcast(
                AttackEventMessage(data=event.data)
            )

        stats_task = asyncio.create_task(stats_loop())
        try:
            await scheduler.run(broadcast, stop=self._stop)
        finally:
            stats_task.cancel()
            await asyncio.gather(stats_task, return_exceptions=True)

    async def _load_pairs(self) -> list[AttackPair]:
        pairs: list[AttackPair] = []
        for layer in (Layer.L3, Layer.L7):
            try:
                observation = await self._repository.latest_observation(
                    _ENDPOINT_ATTACKS[layer], layer
                )
            except Exception as exc:
                logger.warning(
                    "Error fetching latest observation for layer %s: %s",
                    layer,
                    exc,
                )
                continue
            if observation is None:
                continue
            try:
                rows = await self._repository.attack_pairs_for_observation(
                    observation.id
                )
            except Exception as exc:
                logger.warning(
                    "Error fetching attack pairs for observation %s: %s",
                    observation.id,
                    exc,
                )
                continue
            pairs.extend(
                AttackPair(
                    layer=Layer(row.layer),
                    source_country_code=row.source_country_code,
                    source_country_name=row.source_country_name,
                    target_country_code=row.target_country_code,
                    target_country_name=row.target_country_name,
                    share=row.share,
                    rank=row.rank,
                    unit=Unit(row.unit),
                )
                for row in rows
            )
        return pairs
