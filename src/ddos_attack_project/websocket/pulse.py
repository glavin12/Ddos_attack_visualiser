"""Backend-driven Radar pulse — pushes 24h aggregates over WebSocket.

The pulse is the server-side heartbeat of the globe's arc layer: on a fixed
cadence (and immediately after each successful Radar refresh, via the
ingestor's ``on_refresh`` callback) the broadcaster reads the newest
persisted top-attacks observations for both layers and pushes them to
every connected WebSocket client. Clients that just connected receive one
pulse right after the welcome envelope.

Nothing is ever fabricated: until the first real Radar observation has
been persisted for a layer, that layer is simply absent from the pulse —
and no pulse at all is sent while neither layer has data.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import EndpointKey, Layer
from ddos_attack_project.websocket.envelopes import (
    RadarPulseData,
    RadarPulseLayerData,
    RadarPulseMessage,
    RadarPulseRoute,
)
from ddos_attack_project.websocket.manager import ConnectionManager

logger = logging.getLogger(__name__)

_PULSE_ENDPOINTS = {
    Layer.L3: EndpointKey.L3_TOP_ATTACKS,
    Layer.L7: EndpointKey.L7_TOP_ATTACKS,
}


class WebSocketLike(Protocol):
    """Minimal shape needed to send to one client (fastapi.WebSocket)."""

    async def send_json(self, payload: dict) -> None: ...


class RadarPulseBroadcaster:
    """Periodically pushes the latest Radar top-route aggregates to clients."""

    def __init__(
        self,
        repository: ObservationRepository,
        manager: ConnectionManager,
        *,
        interval_seconds: float = 30.0,
        max_routes_per_layer: int = 30,
    ) -> None:
        self._repository = repository
        self._manager = manager
        self._interval_seconds = interval_seconds
        self._max_routes = max_routes_per_layer
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the heartbeat loop."""
        if self._task is not None:
            raise RuntimeError("pulse broadcaster is already running")
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="radar-pulse")

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None:
            await asyncio.wait([self._task])
            self._task = None

    async def on_radar_refresh(self, refresh_id: str) -> None:
        """``RadarIngestor.on_refresh`` callback — pulse out a fresh refresh."""
        await self.pulse_once()

    async def pulse_once(self) -> RadarPulseData | None:
        """Build a pulse from the latest observations and broadcast it.

        Returns the broadcast data, or ``None`` when no layer has a
        persisted observation yet (nothing real to show — never fabricate).
        """
        data = await self.build_pulse()
        if data is None:
            return None
        await self._manager.broadcast_radar_pulse(data)
        return data

    async def send_to(self, websocket: WebSocketLike) -> None:
        """Push the latest pulse to a single client (on WS connect)."""
        data = await self.build_pulse()
        if data is None:
            return
        await self._manager.send_to(websocket, RadarPulseMessage(data=data))

    async def build_pulse(self) -> RadarPulseData | None:
        """Assemble the pulse payload from the latest observations."""
        layers: dict[str, RadarPulseLayerData] = {}
        for layer, endpoint_key in _PULSE_ENDPOINTS.items():
            observation = await self._repository.latest_observation(
                endpoint_key, layer
            )
            if observation is None:
                continue
            pairs = await self._repository.attack_pairs_for_observation(
                observation.id
            )
            layers[layer.value] = RadarPulseLayerData(
                collected_at=observation.collected_at,
                observation_start=observation.window_start,
                observation_end=observation.window_end,
                routes=[_pulse_route(row) for row in pairs[: self._max_routes]],
            )
        if not layers:
            return None
        return RadarPulseData(
            l3=layers.get(Layer.L3.value),
            l7=layers.get(Layer.L7.value),
        )

    async def _run(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._interval_seconds
                )
                return  # stop was set
            except asyncio.TimeoutError:
                pass

            # Skip the database round-trip while nobody is listening; the
            # on_refresh callback still fires for fresh data.
            if self._manager.connection_count == 0:
                continue

            try:
                await self.pulse_once()
            except Exception:
                logger.exception("Radar pulse broadcast failed")


def _pulse_route(row: orm.AttackPair) -> RadarPulseRoute:
    return RadarPulseRoute(
        source={"code": row.source_country_code, "name": row.source_country_name},
        target={"code": row.target_country_code, "name": row.target_country_name},
        share=float(row.share),
        rank=row.rank,
    )


__all__ = ["RadarPulseBroadcaster"]
