"""Pytest fixtures for API/service tests using in-memory SQLite."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ddos_attack_project.db import models as orm
from ddos_attack_project.db.mappers import dataset_to_rows
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import EndpointKey
from ddos_attack_project.radar.adapters import adapt
from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
)
from pydantic import TypeAdapter

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"

_COLLECTED_AT = datetime.now(UTC)

_RESULT_ADAPTERS = {
    EndpointKey.L3_TOP_ATTACKS: TypeAdapter(CloudflareTopAttacksResult),
    EndpointKey.L7_TOP_ATTACKS: TypeAdapter(CloudflareTopAttacksResult),
    EndpointKey.L3_TOP_ORIGIN: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L3_TOP_TARGET: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L7_TOP_ORIGIN: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L7_TOP_TARGET: TypeAdapter(CloudflareTopLocationsResult),
    EndpointKey.L3_SUMMARY_PROTOCOL: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L3_SUMMARY_VECTOR: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L7_SUMMARY_HTTP_METHOD: TypeAdapter(CloudflareSummaryResult),
    EndpointKey.L3_TIMESERIES: TypeAdapter(CloudflareTimeSeriesResult),
    EndpointKey.L7_TIMESERIES: TypeAdapter(CloudflareTimeSeriesResult),
}


def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    assert path.exists(), f"missing fixture {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def build_dataset(endpoint_key: EndpointKey, refresh_id: str):
    data = load_fixture(endpoint_key.value)
    envelope = CloudflareEnvelope.model_validate(data)
    result = _RESULT_ADAPTERS[endpoint_key].validate_python(envelope.result)
    return adapt(
        endpoint_key,
        result,
        refresh_id=refresh_id,
        collected_at=_COLLECTED_AT,
    )


async def seed_full_refresh(session_factory) -> str:
    """Persist a full refresh for both layers and return its refresh_id."""
    repo = ObservationRepository(session_factory)
    refresh_id = str(uuid4())
    datasets = [
        build_dataset(key, refresh_id)
        for key in EndpointKey
    ]
    await repo.save_refresh(datasets)
    return refresh_id


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(orm.Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_session_factory(session_factory):
    await seed_full_refresh(session_factory)
    return session_factory


class NullIngestor:
    """No-op ingestor for tests — never talks to any external service."""

    async def start(self) -> None:  # pragma: no cover - trivial
        return None

    async def stop(self) -> None:  # pragma: no cover - trivial
        return None
