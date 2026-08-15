"""Tests for the ObservationRepository using in-memory SQLite."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import (
    EndpointKey,
    Layer,
    Unit,
)
from ddos_attack_project.domain.models import AttackPair, RadarDataset
from ddos_attack_project.radar.adapters import adapt
from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareTopAttacksResult,
)

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"

_COLLECTED_AT = datetime.now(UTC)


def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    assert path.exists(), f"missing fixture {path}"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(orm.Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def build_l3_attacks_dataset() -> RadarDataset:
    data = load_fixture("layer3-top-attacks")
    envelope = CloudflareEnvelope.model_validate(data)
    result = CloudflareTopAttacksResult.model_validate(envelope.result)
    return adapt(
        EndpointKey.L3_TOP_ATTACKS,
        result,
        refresh_id=str(uuid4()),
        collected_at=_COLLECTED_AT,
    )


async def test_save_and_query_refresh(session_factory) -> None:
    repo = ObservationRepository(session_factory)
    dataset = build_l3_attacks_dataset()

    refresh_id = await repo.save_refresh([dataset])
    assert refresh_id == str(dataset.observation.refresh_id)

    observation = await repo.latest_observation(
        EndpointKey.L3_TOP_ATTACKS, Layer.L3
    )
    assert observation is not None
    assert observation.refresh_id == dataset.observation.refresh_id

    pairs = await repo.attack_pairs_for_observation(observation.id)
    assert len(pairs) == 100
    assert pairs[0].share > pairs[-1].share


async def test_save_refresh_requires_shared_refresh_id(
    session_factory,
) -> None:
    repo = ObservationRepository(session_factory)
    first = build_l3_attacks_dataset()
    second = build_l3_attacks_dataset()

    with pytest.raises(ValueError):
        await repo.save_refresh([first, second])


async def test_save_empty_refresh_rejected(session_factory) -> None:
    repo = ObservationRepository(session_factory)
    with pytest.raises(ValueError):
        await repo.save_refresh([])


async def test_save_refresh_is_atomic_on_failure(session_factory) -> None:
    repo = ObservationRepository(session_factory)
    good = build_l3_attacks_dataset()
    bad = RadarDataset(
        observation=good.observation.model_copy(update={"id": "duplicate-id"}),
        pairs=[
            AttackPair(
                layer=Layer.L3,
                source_country_code="BR",
                target_country_code="US",
                share=0.1,
                unit=Unit.BYTES,
            )
        ],
    )
    # Make the bad dataset collide on the observation primary key.
    good.observation = good.observation.model_copy(update={"id": "duplicate-id"})

    with pytest.raises(Exception):
        await repo.save_refresh([good, bad])

    async with session_factory() as session:
        count = await session.scalar(select(orm.RadarObservation))
    assert count is None


async def test_latest_observation_window_filtering(session_factory) -> None:
    repo = ObservationRepository(session_factory)
    dataset = build_l3_attacks_dataset()
    await repo.save_refresh([dataset])

    recent = await repo.latest_observation_window(
        Layer.L3,
        max_age=_COLLECTED_AT,
    )
    assert recent is not None

    future = _COLLECTED_AT.replace(year=_COLLECTED_AT.year + 1)
    stale = await repo.latest_observation_window(Layer.L3, max_age=future)
    assert stale is None


async def test_dataset_rows_units_mapped(session_factory) -> None:
    repo = ObservationRepository(session_factory)
    dataset = build_l3_attacks_dataset()
    await repo.save_refresh([dataset])

    async with session_factory() as session:
        row = await session.scalar(
            select(orm.AttackPair)
        )
    assert row is not None
    assert row.unit == Unit.BYTES
    assert row.source_country_code == "BR"
