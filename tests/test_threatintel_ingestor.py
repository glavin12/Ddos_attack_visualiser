"""End-to-end tests for the ThreatIntelIngestor with fake adapters + geoip."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ddos_attack_project.config import AppSettings
from ddos_attack_project.db import models as orm
from ddos_attack_project.db.repositories import ThreatIndicatorRepository
from ddos_attack_project.threatintel.geoip import GeoIPService, GeoLocation
from ddos_attack_project.threatintel.ingestor import ThreatIntelIngestor
from ddos_attack_project.threatintel.sources.base import RawIndicator


class _FakeAdapter:
    def __init__(self, source_feed: str, indicators: list[RawIndicator]) -> None:
        self.source_feed = source_feed
        self._indicators = list(indicators)
        self.fetch_calls = 0

    async def fetch(self) -> list[RawIndicator]:
        self.fetch_calls += 1
        return list(self._indicators)


class _FakeGeoIP(GeoIPService):
    """Bypass the real MaxMind lookup and return canned locations."""

    def __init__(self, table: dict[str, GeoLocation]) -> None:
        super().__init__(db_path=None)
        self._table = table

    def lookup(self, ip: str) -> GeoLocation | None:
        return self._table.get(ip)


def _settings(**overrides) -> AppSettings:
    base = {
        "database_url": "sqlite+aiosqlite:///:memory:",
        "cf_api_token": "cf-token",
        "threatintel_greynoise_enrichment_top_n": 0,
        "threatintel_poll_urlhaus_seconds": 60,
        "threatintel_poll_feodo_seconds": 60,
        "threatintel_poll_threatfox_seconds": 60,
        "threatintel_prune_interval_seconds": 3600,
    }
    base.update(overrides)
    return AppSettings.model_validate(base)


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(orm.Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def test_poll_source_persists_and_geolocates(session_factory) -> None:
    now = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)
    raw = [
        RawIndicator(
            indicator="1.1.1.1",
            indicator_type="ip",
            host="1.1.1.1",
            threat_family="Emotet",
            first_seen=now,
            last_seen=now,
            source_url="https://feodotracker.abuse.ch/browse/host/1.1.1.1/",
        ),
    ]
    adapter = _FakeAdapter("feodo", raw)
    geoip = _FakeGeoIP(
        {
            "1.1.1.1": GeoLocation(
                country_code="US", country_name="United States",
                city="San Francisco", latitude=37.77, longitude=-122.42,
            )
        }
    )
    repo = ThreatIndicatorRepository(session_factory)
    ingestor = ThreatIntelIngestor(
        settings=_settings(),
        repository=repo,
        adapters=[adapter],
        geoip=geoip,
    )

    inserted, updated = await ingestor.poll_source(adapter)
    assert len(inserted) == 1
    assert len(updated) == 0
    assert inserted[0].city == "San Francisco"

    rows = await repo.recent_indicators()
    assert len(rows) == 1
    row = rows[0]
    assert row.country_code == "US"
    assert row.city == "San Francisco"
    assert row.latitude == 37.77


async def test_poll_source_calls_broadcast_only_for_new(session_factory) -> None:
    now = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)
    later = now + timedelta(hours=1)
    raw_a = RawIndicator(
        indicator="2.2.2.2", indicator_type="ip", host="2.2.2.2",
        threat_family=None, first_seen=now, last_seen=now, source_url=None,
    )
    raw_b = RawIndicator(
        indicator="2.2.2.2", indicator_type="ip", host="2.2.2.2",
        threat_family="TrickBot", first_seen=now, last_seen=later, source_url=None,
    )

    broadcasts: list[list[str]] = []

    async def on_new(indicators):
        broadcasts.append([i.indicator for i in indicators])

    repo = ThreatIndicatorRepository(session_factory)
    geoip = _FakeGeoIP({})
    adapter = _FakeAdapter("feodo", [raw_a])
    ingestor = ThreatIntelIngestor(
        settings=_settings(),
        repository=repo,
        adapters=[adapter],
        geoip=geoip,
        on_new_indicators=on_new,
    )

    scheduler = ingestor.schedulers if hasattr(ingestor, "schedulers") else []
    # First cycle: one insert -> broadcast fires with one indicator.
    from ddos_attack_project.threatintel.ingestor import SourceScheduler

    sched = SourceScheduler(adapter=adapter, interval_seconds=60, cycle=ingestor._run_source_cycle)
    await ingestor._run_source_cycle(sched)
    assert broadcasts == [["2.2.2.2"]]

    # Second cycle sees the same IOC with an updated last_seen — no broadcast.
    adapter._indicators = [raw_b]
    await ingestor._run_source_cycle(sched)
    assert broadcasts == [["2.2.2.2"]]  # unchanged


async def test_ingestor_skips_indicator_with_no_geo_hostname(
    session_factory,
) -> None:
    now = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)
    # Hostname that will never resolve (invalid TLD, no DNS record).
    raw = [
        RawIndicator(
            indicator="http://this-domain-does-not-exist-6f7e.invalid/x",
            indicator_type="url",
            host="this-domain-does-not-exist-6f7e.invalid",
            threat_family=None, first_seen=now, last_seen=now, source_url=None,
        ),
    ]
    adapter = _FakeAdapter("urlhaus", raw)
    repo = ThreatIndicatorRepository(session_factory)
    ingestor = ThreatIntelIngestor(
        settings=_settings(),
        repository=repo,
        adapters=[adapter],
        geoip=_FakeGeoIP({}),
    )
    inserted, updated = await ingestor.poll_source(adapter)
    assert inserted == []
    assert updated == []


async def test_prune_removes_stale_rows_via_ingestor(session_factory) -> None:
    """The prune loop uses the same cutoff logic and touches the same table."""
    old = datetime.now(UTC) - timedelta(days=30)
    fresh = datetime.now(UTC)

    repo = ThreatIndicatorRepository(session_factory)
    raw_old = RawIndicator(
        indicator="3.3.3.3", indicator_type="ip", host="3.3.3.3",
        threat_family=None, first_seen=old, last_seen=old, source_url=None,
    )
    raw_fresh = RawIndicator(
        indicator="4.4.4.4", indicator_type="ip", host="4.4.4.4",
        threat_family=None, first_seen=fresh, last_seen=fresh, source_url=None,
    )
    adapter = _FakeAdapter("feodo", [raw_old, raw_fresh])
    geoip = _FakeGeoIP({})
    ingestor = ThreatIntelIngestor(
        settings=_settings(threatintel_prune_after_days=7),
        repository=repo,
        adapters=[adapter],
        geoip=geoip,
    )
    await ingestor.poll_source(adapter)

    # Simulate the loop's body once.
    cutoff = datetime.now(UTC) - timedelta(days=7)
    deleted = await repo.prune_older_than(cutoff)
    assert deleted == 1

    rows = await repo.recent_indicators()
    assert len(rows) == 1
    assert rows[0].indicator == "4.4.4.4"
