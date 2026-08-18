"""Tests for the distinct error signals contract in api/service.py.

Contract:
- 200 with empty entries + null observation.collected_at → "no data yet".
- 503 with body.status = "backend_error" → the data store failed.
"""

from __future__ import annotations

import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager
from sqlalchemy.exc import OperationalError

from ddos_attack_project.main import create_app

from tests.conftest import NullIngestor


class ExplodingRepository:
    """Repository stub that raises a DB error on every method."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    async def _boom(self, *_args, **_kwargs):
        raise OperationalError("SELECT ...", {}, Exception("connection refused"))

    latest_observation = _boom
    latest_observation_window = _boom
    attack_pairs_for_observation = _boom
    distributions_for_observation = _boom
    characteristics_for_observation = _boom
    timeseries_for_observation = _boom


@pytest_asyncio.fixture
async def app(session_factory, monkeypatch):
    # Swap the ObservationRepository FastAPI wires up for one that always fails.
    monkeypatch.setattr(
        "ddos_attack_project.main.ObservationRepository", ExplodingRepository
    )
    return create_app(
        session_factory=session_factory,
        ingestor=NullIngestor(),
        threatintel_ingestor=NullIngestor(),
    )


@pytest_asyncio.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def test_backend_error_returns_503_with_status_body(client) -> None:
    response = await client.get("/api/v1/radar/attacks", params={"layer": "L3"})
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "backend_error"


async def test_status_endpoint_also_returns_503_on_backend_error(client) -> None:
    response = await client.get("/api/v1/radar/status")
    assert response.status_code == 503
    assert response.json()["status"] == "backend_error"


async def test_health_still_returns_200_when_db_is_down(client) -> None:
    """Health is deliberately independent of the data store."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
