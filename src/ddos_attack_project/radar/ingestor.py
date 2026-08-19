"""Scheduled Radar poller that persists normalized observations.

One poll cycle fetches every registered endpoint, adapts each response into a
canonical dataset, and saves the successful datasets atomically as one
refresh. Per-endpoint failures are logged and skipped; a whole cycle only
fails to save when every endpoint failed.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from ddos_attack_project.config import AppSettings
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import EndpointKey
from ddos_attack_project.domain.models import RadarDataset
from ddos_attack_project.radar.adapters import adapt
from ddos_attack_project.radar.client import ENDPOINTS, RadarClient

logger = logging.getLogger(__name__)


_ATTACK_ENDPOINTS = {
    EndpointKey.L3_TOP_ATTACKS,
    EndpointKey.L7_TOP_ATTACKS,
}
_LOCATION_ENDPOINTS = {
    EndpointKey.L3_TOP_ORIGIN,
    EndpointKey.L3_TOP_TARGET,
    EndpointKey.L7_TOP_ORIGIN,
    EndpointKey.L7_TOP_TARGET,
}
_TIMESERIES_ENDPOINTS = {
    EndpointKey.L3_TIMESERIES,
    EndpointKey.L7_TIMESERIES,
}


class RadarIngestor:
    """Owns the periodic Radar poll for the application lifespan."""

    def __init__(
        self,
        client: RadarClient,
        repository: ObservationRepository,
        settings: AppSettings,
        *,
        initial_poll_timeout_seconds: float = 60.0,
        on_refresh: Callable[[str], Awaitable[None]] | None = None,
    ) -> None:
        self._client = client
        self._repository = repository
        self._settings = settings
        self._initial_timeout = initial_poll_timeout_seconds
        self._on_refresh = on_refresh
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None
        self._last_success_at: datetime | None = None
        self._last_error: str | None = None
        self._last_refresh_id: str | None = None
        self._last_endpoint_failures: list[tuple[EndpointKey, str]] = []

    @property
    def last_success_at(self) -> datetime | None:
        return self._last_success_at

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def last_refresh_id(self) -> str | None:
        return self._last_refresh_id

    @property
    def last_endpoint_failures(self) -> list[tuple[EndpointKey, str]]:
        return list(self._last_endpoint_failures)

    async def start(self) -> None:
        """Run an initial poll (bounded), then start the background loop."""
        if self._task is not None:
            raise RuntimeError("ingestor is already running")
        self._stop_event = asyncio.Event()

        try:
            await asyncio.wait_for(
                self.poll_once(), timeout=self._initial_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Initial Radar poll exceeded %.0fs; falling back to background",
                self._initial_timeout,
            )
        except Exception:
            logger.exception(
                "Initial Radar poll raised; falling back to background"
            )

        self._task = asyncio.create_task(self._run(), name="radar-ingestor")

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None:
            await asyncio.wait([self._task])
            self._task = None

    async def poll_once(self) -> str | None:
        """Fetch every endpoint and persist successful datasets as one refresh.

        Returns the persisted ``refresh_id`` if at least one endpoint
        succeeded and was written; ``None`` otherwise.
        """
        refresh_id = str(uuid.uuid4())
        collected_at = datetime.now(UTC)
        datasets: list[RadarDataset] = []
        failures: list[tuple[EndpointKey, str]] = []

        for endpoint_key, endpoint in ENDPOINTS.items():
            try:
                result = await self._client.fetch(
                    endpoint,
                    date_range=self._date_range_for(endpoint_key),
                    limit=self._limit_for(endpoint_key),
                    extra=self._extra_for(endpoint_key),
                )
                datasets.append(
                    adapt(
                        endpoint_key,
                        result,
                        refresh_id=refresh_id,
                        collected_at=collected_at,
                    )
                )
            except Exception as exc:
                failures.append((endpoint_key, repr(exc)))
                logger.warning(
                    "Radar ingest failed for %s: %s", endpoint_key.value, exc
                )

        self._last_endpoint_failures = failures

        if not datasets:
            self._last_error = f"all {len(ENDPOINTS)} endpoints failed"
            logger.error(
                "Radar ingest cycle produced no datasets (all endpoints failed)"
            )
            return None

        try:
            saved_id = await self._repository.save_refresh(datasets)
        except Exception as exc:
            self._last_error = f"save_refresh failed: {exc!r}"
            logger.exception("Radar ingest save_refresh failed")
            return None

        self._last_success_at = collected_at
        self._last_refresh_id = saved_id
        self._last_error = None
        logger.info(
            "Radar ingest complete: refresh=%s endpoints=%d/%d failures=%d",
            saved_id,
            len(datasets),
            len(ENDPOINTS),
            len(failures),
        )

        if self._on_refresh is not None:
            try:
                await self._on_refresh(saved_id)
            except Exception:
                # A failed post-refresh hook must never fail the poll itself.
                logger.exception("Radar on_refresh callback failed")
        return saved_id

    async def _run(self) -> None:
        assert self._stop_event is not None
        interval = float(self._settings.radar_refresh_seconds)
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=interval
                )
                return  # stop was set
            except asyncio.TimeoutError:
                pass

            try:
                await self.poll_once()
            except Exception:
                logger.exception("Unexpected error in Radar ingest cycle")

    def _date_range_for(self, endpoint_key: EndpointKey) -> str:
        if endpoint_key in _TIMESERIES_ENDPOINTS:
            return self._settings.radar_history_date_range
        return self._settings.radar_date_range

    def _limit_for(self, endpoint_key: EndpointKey) -> int | None:
        if endpoint_key in _ATTACK_ENDPOINTS:
            return self._settings.radar_attacks_limit
        if endpoint_key in _LOCATION_ENDPOINTS:
            return self._settings.radar_locations_limit
        return None

    def _extra_for(self, endpoint_key: EndpointKey) -> dict[str, str] | None:
        if endpoint_key in _TIMESERIES_ENDPOINTS:
            return {"aggInterval": self._settings.radar_history_agg_interval}
        return None
