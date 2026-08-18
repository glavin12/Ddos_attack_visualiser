"""Orchestrating ingestor for public threat-intel feeds.

One coordinator per source runs on its own interval. Each cycle:
- fetches raw indicators from the source
- resolves hostnames to IPs and geolocates via MaxMind
- optionally enriches the top-N newest with GreyNoise Community
- upserts them to the ``threat_indicators`` table
- optionally invokes a broadcast callback for newly-inserted indicators

A single prune task runs alongside and deletes rows older than the
configured retention window (default 7 days).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Sequence

from ddos_attack_project.config import AppSettings
from ddos_attack_project.db.repositories import ThreatIndicatorRepository
from ddos_attack_project.domain.enums import IndicatorType, SourceFeed
from ddos_attack_project.domain.models import ThreatIndicator
from ddos_attack_project.threatintel.enrichment import GreyNoiseEnricher
from ddos_attack_project.threatintel.geoip import GeoIPService
from ddos_attack_project.threatintel.sources.base import (
    RawIndicator,
    resolve_hostname,
)

logger = logging.getLogger(__name__)


BroadcastCallback = Callable[[list[ThreatIndicator]], Awaitable[None]]


class SourceScheduler:
    """Runs one source on its own interval; owned by the ingestor."""

    def __init__(
        self,
        adapter,
        interval_seconds: float,
        cycle: Callable[["SourceScheduler"], Awaitable[None]],
    ) -> None:
        self.adapter = adapter
        self.interval_seconds = interval_seconds
        self._cycle = cycle
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task[None] | None = None
        self.last_success_at: datetime | None = None
        self.last_error: str | None = None
        self.last_inserted: int = 0
        self.last_updated: int = 0

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(
            self._run(), name=f"threatintel-{self.adapter.source_feed}"
        )

    async def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None:
            await asyncio.wait([self._task])
            self._task = None

    async def _run(self) -> None:
        assert self._stop_event is not None
        try:
            await self._cycle(self)
        except Exception:
            logger.exception(
                "First cycle failed for %s", self.adapter.source_feed
            )
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self.interval_seconds
                )
                return
            except asyncio.TimeoutError:
                pass
            try:
                await self._cycle(self)
            except Exception:
                logger.exception(
                    "Cycle failed for %s", self.adapter.source_feed
                )


class ThreatIntelIngestor:
    """Owns the periodic threat-intel polls for the application lifespan."""

    def __init__(
        self,
        *,
        settings: AppSettings,
        repository: ThreatIndicatorRepository,
        adapters: Sequence,
        geoip: GeoIPService,
        greynoise: GreyNoiseEnricher | None = None,
        on_new_indicators: BroadcastCallback | None = None,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._adapters = list(adapters)
        self._geoip = geoip
        self._greynoise = greynoise
        self._on_new_indicators = on_new_indicators
        self._schedulers: list[SourceScheduler] = []
        self._prune_task: asyncio.Task[None] | None = None
        self._prune_stop: asyncio.Event | None = None

    @property
    def schedulers(self) -> list[SourceScheduler]:
        return list(self._schedulers)

    async def start(self) -> None:
        interval_map = {
            SourceFeed.URLHAUS: self._settings.threatintel_poll_urlhaus_seconds,
            SourceFeed.FEODO: self._settings.threatintel_poll_feodo_seconds,
            SourceFeed.THREATFOX: self._settings.threatintel_poll_threatfox_seconds,
        }
        for adapter in self._adapters:
            scheduler = SourceScheduler(
                adapter=adapter,
                interval_seconds=float(
                    interval_map.get(SourceFeed(adapter.source_feed), 300)
                ),
                cycle=self._run_source_cycle,
            )
            self._schedulers.append(scheduler)
            await scheduler.start()

        self._prune_stop = asyncio.Event()
        self._prune_task = asyncio.create_task(
            self._run_prune_loop(), name="threatintel-prune"
        )

    async def stop(self) -> None:
        for scheduler in self._schedulers:
            await scheduler.stop()
        self._schedulers.clear()
        if self._prune_stop is not None:
            self._prune_stop.set()
        if self._prune_task is not None:
            await asyncio.wait([self._prune_task])
            self._prune_task = None

    async def poll_source(self, adapter) -> tuple[list[ThreatIndicator], list[ThreatIndicator]]:
        """One end-to-end poll for a single source. Returns (inserted, updated)."""
        raw = await adapter.fetch()
        if not raw:
            return ([], [])
        enriched = await self._enrich(raw, source_feed=adapter.source_feed)
        if not enriched:
            return ([], [])
        return await self._persist(enriched)

    async def _run_source_cycle(self, scheduler: SourceScheduler) -> None:
        try:
            inserted, updated = await self.poll_source(scheduler.adapter)
        except Exception as exc:
            scheduler.last_error = repr(exc)
            raise
        scheduler.last_inserted = len(inserted)
        scheduler.last_updated = len(updated)
        scheduler.last_success_at = datetime.now(UTC)
        scheduler.last_error = None
        logger.info(
            "threatintel[%s]: inserted=%d updated=%d",
            scheduler.adapter.source_feed,
            len(inserted),
            len(updated),
        )
        if inserted and self._on_new_indicators is not None:
            try:
                await self._on_new_indicators(inserted)
            except Exception:
                logger.exception(
                    "Broadcast callback failed for %d new indicators",
                    len(inserted),
                )

    async def _enrich(
        self, raw: list[RawIndicator], *, source_feed: str
    ) -> list[ThreatIndicator]:
        indicators: list[ThreatIndicator] = []
        # Newest first so GreyNoise enrichment lands on the freshest.
        raw_sorted = sorted(raw, key=lambda r: r.last_seen, reverse=True)
        max_gn = self._settings.threatintel_greynoise_enrichment_top_n
        for index, item in enumerate(raw_sorted):
            resolved_ip = await resolve_hostname(item.host)
            if resolved_ip is None:
                continue
            geo = self._geoip.lookup(resolved_ip)
            gn_class = None
            gn_tags = None
            if self._greynoise is not None and index < max_gn:
                info = await self._greynoise.lookup(resolved_ip)
                if info is not None:
                    gn_class = info.classification
                    gn_tags = info.tags
            try:
                indicators.append(
                    ThreatIndicator(
                        source_feed=SourceFeed(source_feed),
                        indicator=item.indicator,
                        indicator_type=IndicatorType(item.indicator_type),
                        resolved_ip=resolved_ip,
                        country_code=geo.country_code if geo else None,
                        country_name=geo.country_name if geo else None,
                        city=geo.city if geo else None,
                        latitude=geo.latitude if geo else None,
                        longitude=geo.longitude if geo else None,
                        threat_family=item.threat_family,
                        first_seen=item.first_seen,
                        last_seen=item.last_seen,
                        greynoise_classification=gn_class,
                        greynoise_tags=gn_tags,
                        source_url=item.source_url,
                    )
                )
            except Exception:
                logger.debug(
                    "Skipping malformed indicator %r", item.indicator, exc_info=True
                )
        return indicators

    async def _persist(
        self, indicators: list[ThreatIndicator]
    ) -> tuple[list[ThreatIndicator], list[ThreatIndicator]]:
        keys = [(ind.source_feed, ind.indicator) for ind in indicators]
        existing = await self._existing_keys(keys)
        inserted = [
            ind
            for ind in indicators
            if (ind.source_feed, ind.indicator) not in existing
        ]
        updated = [
            ind
            for ind in indicators
            if (ind.source_feed, ind.indicator) in existing
        ]
        await self._repository.upsert_indicators(indicators)
        return (inserted, updated)

    async def _existing_keys(
        self, keys: list[tuple[str, str]]
    ) -> set[tuple[str, str]]:
        if not keys:
            return set()
        source_feeds = {k[0] for k in keys}
        indicator_values = {k[1] for k in keys}
        seen: set[tuple[str, str]] = set()
        for feed in source_feeds:
            rows = await self._repository.recent_indicators(
                source_feed=feed, limit=10_000
            )
            for row in rows:
                if row.indicator in indicator_values:
                    seen.add((row.source_feed, row.indicator))
        return seen

    async def _run_prune_loop(self) -> None:
        assert self._prune_stop is not None
        interval = float(self._settings.threatintel_prune_interval_seconds)
        while not self._prune_stop.is_set():
            try:
                await asyncio.wait_for(
                    self._prune_stop.wait(), timeout=interval
                )
                return
            except asyncio.TimeoutError:
                pass
            try:
                cutoff = datetime.now(UTC) - timedelta(
                    days=self._settings.threatintel_prune_after_days
                )
                deleted = await self._repository.prune_older_than(cutoff)
                if deleted:
                    logger.info(
                        "threatintel prune: deleted %d rows older than %s",
                        deleted,
                        cutoff.isoformat(),
                    )
            except Exception:
                logger.exception("threatintel prune failed")
