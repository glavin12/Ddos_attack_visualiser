"""Tests for the ThreatIndicatorRepository (upsert, list, prune)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.repositories import ThreatIndicatorRepository
from ddos_attack_project.domain.enums import IndicatorType, SourceFeed
from ddos_attack_project.domain.models import ThreatIndicator


def _naive(dt: datetime) -> datetime:
    """Strip tzinfo so wall-clock compares work across SQLite (naive) and Postgres (aware)."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(orm.Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def _indicator(
    source_feed: SourceFeed = SourceFeed.URLHAUS,
    indicator: str = "http://bad.example/malware.bin",
    *,
    first_seen: datetime | None = None,
    last_seen: datetime | None = None,
    threat_family: str | None = None,
    country_code: str | None = "NL",
    city: str | None = "Rotterdam",
    latitude: float | None = 51.92,
    longitude: float | None = 4.48,
    resolved_ip: str = "89.185.85.42",
) -> ThreatIndicator:
    now = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    return ThreatIndicator(
        source_feed=source_feed,
        indicator=indicator,
        indicator_type=IndicatorType.URL,
        resolved_ip=resolved_ip,
        country_code=country_code,
        country_name="Netherlands" if country_code == "NL" else None,
        city=city,
        latitude=latitude,
        longitude=longitude,
        threat_family=threat_family,
        first_seen=first_seen or now,
        last_seen=last_seen or now,
        source_url="https://urlhaus.abuse.ch/url/12345/",
    )


async def test_upsert_inserts_new_indicators(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    inserted, updated = await repo.upsert_indicators([_indicator()])
    assert inserted == 1
    assert updated == 0

    rows = await repo.recent_indicators()
    assert len(rows) == 1
    assert rows[0].indicator == "http://bad.example/malware.bin"
    assert rows[0].city == "Rotterdam"


async def test_upsert_updates_existing_indicator(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    t0 = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    t1 = datetime(2026, 8, 19, 14, 30, tzinfo=UTC)

    await repo.upsert_indicators(
        [_indicator(first_seen=t0, last_seen=t0, threat_family=None)]
    )
    inserted, updated = await repo.upsert_indicators(
        [_indicator(first_seen=t1, last_seen=t1, threat_family="Emotet")]
    )
    assert inserted == 0
    assert updated == 1

    rows = await repo.recent_indicators()
    assert len(rows) == 1
    row = rows[0]
    # SQLite returns naive datetimes; production Postgres preserves tz. Compare
    # the wall-clock components rather than tzinfo-attached identity.
    assert _naive(row.last_seen) == _naive(t1)
    assert _naive(row.first_seen) == _naive(t0)  # never regresses forward
    assert row.threat_family == "Emotet"


async def test_upsert_never_regresses_last_seen(session_factory) -> None:
    """A stale re-observation must not roll last_seen backwards."""
    repo = ThreatIndicatorRepository(session_factory)
    fresh = datetime(2026, 8, 19, 15, 0, tzinfo=UTC)
    stale = datetime(2026, 8, 19, 10, 0, tzinfo=UTC)

    await repo.upsert_indicators(
        [_indicator(first_seen=fresh, last_seen=fresh)]
    )
    await repo.upsert_indicators(
        [_indicator(first_seen=stale, last_seen=stale)]
    )
    rows = await repo.recent_indicators()
    assert _naive(rows[0].last_seen) == _naive(fresh)
    assert _naive(rows[0].first_seen) == _naive(stale)  # first_seen extends backward


async def test_upsert_preserves_prior_enrichment(session_factory) -> None:
    """A later observation with missing enrichment must not wipe it."""
    repo = ThreatIndicatorRepository(session_factory)

    await repo.upsert_indicators(
        [_indicator(threat_family="Emotet", city="Rotterdam")]
    )
    await repo.upsert_indicators(
        [
            _indicator(
                threat_family=None, city=None, latitude=None, longitude=None,
                last_seen=datetime(2026, 8, 19, 20, 0, tzinfo=UTC),
            )
        ]
    )
    rows = await repo.recent_indicators()
    assert rows[0].threat_family == "Emotet"
    assert rows[0].city == "Rotterdam"


async def test_upsert_treats_different_feeds_as_distinct(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    inserted, _ = await repo.upsert_indicators(
        [
            _indicator(source_feed=SourceFeed.URLHAUS, indicator="1.2.3.4"),
            _indicator(source_feed=SourceFeed.FEODO, indicator="1.2.3.4"),
        ]
    )
    assert inserted == 2

    rows = await repo.recent_indicators()
    feeds = {row.source_feed for row in rows}
    assert feeds == {"urlhaus", "feodo"}


async def test_recent_indicators_ordering_and_limit(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    base = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)

    payload = [
        _indicator(indicator=f"http://a.example/{i}.bin", last_seen=base + timedelta(minutes=i))
        for i in range(5)
    ]
    await repo.upsert_indicators(payload)

    rows = await repo.recent_indicators(limit=3)
    assert len(rows) == 3
    assert rows[0].indicator == "http://a.example/4.bin"
    assert rows[1].indicator == "http://a.example/3.bin"
    assert rows[2].indicator == "http://a.example/2.bin"


async def test_recent_indicators_filter_by_feed(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    await repo.upsert_indicators(
        [
            _indicator(source_feed=SourceFeed.URLHAUS, indicator="http://a.example/1.bin"),
            _indicator(source_feed=SourceFeed.FEODO, indicator="9.9.9.9"),
        ]
    )
    rows = await repo.recent_indicators(source_feed=SourceFeed.FEODO)
    assert len(rows) == 1
    assert rows[0].indicator == "9.9.9.9"


async def test_prune_older_than_deletes_stale_rows(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    old = datetime(2026, 8, 10, 0, 0, tzinfo=UTC)
    fresh = datetime(2026, 8, 19, 0, 0, tzinfo=UTC)
    cutoff = datetime(2026, 8, 15, 0, 0, tzinfo=UTC)

    await repo.upsert_indicators(
        [
            _indicator(indicator="http://old.example/1.bin", first_seen=old, last_seen=old),
            _indicator(indicator="http://fresh.example/1.bin", first_seen=fresh, last_seen=fresh),
        ]
    )
    deleted = await repo.prune_older_than(cutoff)
    assert deleted == 1

    rows = await repo.recent_indicators()
    assert len(rows) == 1
    assert rows[0].indicator == "http://fresh.example/1.bin"


async def test_upsert_empty_list_is_noop(session_factory) -> None:
    repo = ThreatIndicatorRepository(session_factory)
    inserted, updated = await repo.upsert_indicators([])
    assert (inserted, updated) == (0, 0)
