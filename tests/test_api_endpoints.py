"""Tests for the FastAPI HTTP endpoints."""

from __future__ import annotations

import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager

from ddos_attack_project.main import create_app

from tests.conftest import NullIngestor, seed_full_refresh


@pytest_asyncio.fixture
async def app(session_factory):
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


async def test_health(client) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_radar_status_degraded_when_empty(client) -> None:
    response = await client.get("/api/v1/radar/status")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


async def test_radar_attacks_empty_when_no_data(client) -> None:
    response = await client.get("/api/v1/radar/attacks", params={"layer": "L3"})
    assert response.status_code == 200
    body = response.json()
    assert body["layer"] == "L3"
    assert body["entries"] == []


async def test_radar_attacks_invalid_layer(client) -> None:
    response = await client.get("/api/v1/radar/attacks", params={"layer": "L4"})
    assert response.status_code == 422


async def test_radar_countries_missing_role(client) -> None:
    response = await client.get("/api/v1/radar/countries", params={"layer": "L3"})
    assert response.status_code == 422


async def test_radar_characteristics_invalid_type(client) -> None:
    response = await client.get(
        "/api/v1/radar/characteristics",
        params={"layer": "L3", "type": "bogus"},
    )
    assert response.status_code == 422


async def test_radar_history_invalid_limit(client) -> None:
    response = await client.get(
        "/api/v1/radar/history", params={"layer": "L3", "limit": 0}
    )
    assert response.status_code == 422


async def test_seeded_endpoints(
    session_factory,
) -> None:
    await seed_full_refresh(session_factory)
    app = create_app(
        session_factory=session_factory,
        ingestor=NullIngestor(),
        threatintel_ingestor=NullIngestor(),
    )
    transport = httpx.ASGITransport(app=app)
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            attacks = await client.get(
                "/api/v1/radar/attacks", params={"layer": "L3"}
            )
            assert attacks.status_code == 200
            attacks_body = attacks.json()
            assert len(attacks_body["entries"]) == 100
            assert attacks_body["unit"] == "bytes"

            countries = await client.get(
                "/api/v1/radar/countries",
                params={"layer": "L7", "role": "target"},
            )
            assert countries.status_code == 200
            countries_body = countries.json()
            assert len(countries_body["entries"]) == 50
            assert countries_body["unit"] == "requests"

            characteristics = await client.get(
                "/api/v1/radar/characteristics",
                params={"layer": "L3", "type": "protocol"},
            )
            assert characteristics.status_code == 200
            values = [c["value"] for c in characteristics.json()["entries"]]
            assert "UDP" in values

            history = await client.get(
                "/api/v1/radar/history", params={"layer": "L3"}
            )
            assert history.status_code == 200
            history_body = history.json()
            assert history_body["normalization"] == "MIN0_MAX"
            assert len(history_body["points"]) == 167

            overview = await client.get(
                "/api/v1/radar/overview", params={"layer": "L3"}
            )
            assert overview.status_code == 200
            overview_body = overview.json()
            assert len(overview_body["top_routes"]) == 100
            assert len(overview_body["top_origins"]) == 50
            assert overview_body["observation"]["start"] is not None

            status = await client.get("/api/v1/radar/status")
            assert status.status_code == 200
            assert status.json()["status"] == "healthy"
