"""Tests for the scheduled Radar ingestor."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from ddos_attack_project.config import AppSettings
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.domain.enums import EndpointKey
from ddos_attack_project.radar.client import ENDPOINTS, RadarClient
from ddos_attack_project.radar.ingestor import RadarIngestor

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"


def _fixture_body(endpoint_key: EndpointKey) -> bytes:
    path = FIXTURES / f"{endpoint_key.value}.json"
    assert path.exists(), f"missing fixture {path}"
    return path.read_bytes()


def _endpoint_for_path(path: str) -> EndpointKey | None:
    for key, endpoint in ENDPOINTS.items():
        if endpoint.path == path:
            return key
    return None


def _make_client(handler) -> RadarClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(
        transport=transport,
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
        },
    )
    return RadarClient(
        api_token="test-token",
        base_url="https://api.cloudflare.com/client/v4/radar",
        http_client=http_client,
    )


def _settings(**overrides: Any) -> AppSettings:
    base = {
        "database_url": "sqlite+aiosqlite:///:memory:",
        "cf_api_token": "test-token",
        "radar_refresh_seconds": 30,
    }
    base.update(overrides)
    return AppSettings.model_validate(base)


def _fixture_handler(request: httpx.Request) -> httpx.Response:
    path = "/" + str(request.url.path).split("/radar")[-1].lstrip("/")
    endpoint_key = _endpoint_for_path(path)
    if endpoint_key is None:
        return httpx.Response(404, text=f"no fixture for path {path}")
    return httpx.Response(200, content=_fixture_body(endpoint_key))


async def test_poll_once_persists_every_endpoint(session_factory) -> None:
    client = _make_client(_fixture_handler)
    repo = ObservationRepository(session_factory)
    ingestor = RadarIngestor(client, repo, _settings())

    refresh_id = await ingestor.poll_once()

    assert refresh_id is not None
    assert ingestor.last_error is None
    assert ingestor.last_success_at is not None
    assert ingestor.last_refresh_id == refresh_id
    assert ingestor.last_endpoint_failures == []
    for endpoint_key in EndpointKey:
        layer = "L3" if endpoint_key.value.startswith("layer3") else "L7"
        obs = await repo.latest_observation(endpoint_key, layer)  # type: ignore[arg-type]
        assert obs is not None, f"no observation persisted for {endpoint_key}"
        assert str(obs.refresh_id) == refresh_id

    await client.aclose()


async def test_poll_once_partial_failure_still_saves(session_factory) -> None:
    """One bad endpoint must not sink the whole refresh."""

    failing_key = EndpointKey.L7_TIMESERIES

    def handler(request: httpx.Request) -> httpx.Response:
        path = "/" + str(request.url.path).split("/radar")[-1].lstrip("/")
        endpoint_key = _endpoint_for_path(path)
        if endpoint_key == failing_key:
            return httpx.Response(500, text="upstream boom")
        return _fixture_handler(request)

    client = _make_client(handler)
    repo = ObservationRepository(session_factory)
    ingestor = RadarIngestor(client, repo, _settings())

    refresh_id = await ingestor.poll_once()

    assert refresh_id is not None
    assert ingestor.last_error is None
    failure_keys = {key for key, _ in ingestor.last_endpoint_failures}
    assert failure_keys == {failing_key}

    obs = await repo.latest_observation(failing_key, "L7")  # type: ignore[arg-type]
    assert obs is None

    await client.aclose()


async def test_poll_once_all_failures_returns_none(session_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="everything is on fire")

    client = _make_client(handler)
    repo = ObservationRepository(session_factory)
    ingestor = RadarIngestor(client, repo, _settings())

    refresh_id = await ingestor.poll_once()

    assert refresh_id is None
    assert ingestor.last_error is not None
    assert ingestor.last_success_at is None
    assert len(ingestor.last_endpoint_failures) == len(ENDPOINTS)

    await client.aclose()


async def test_start_stop_runs_background_loop(session_factory) -> None:
    client = _make_client(_fixture_handler)
    repo = ObservationRepository(session_factory)
    # Very small interval so the loop wakes up once during the test.
    ingestor = RadarIngestor(
        client, repo, _settings(radar_refresh_seconds=30),
        initial_poll_timeout_seconds=5.0,
    )

    await ingestor.start()
    assert ingestor.last_refresh_id is not None
    await ingestor.stop()

    await client.aclose()


async def test_timeseries_uses_history_range_and_agg_interval(
    session_factory,
) -> None:
    seen_params: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        path = "/" + str(request.url.path).split("/radar")[-1].lstrip("/")
        endpoint_key = _endpoint_for_path(path)
        if endpoint_key in {EndpointKey.L3_TIMESERIES, EndpointKey.L7_TIMESERIES}:
            seen_params.append(params)
        return _fixture_handler(request)

    client = _make_client(handler)
    repo = ObservationRepository(session_factory)
    ingestor = RadarIngestor(client, repo, _settings())

    await ingestor.poll_once()

    assert len(seen_params) == 2
    for params in seen_params:
        assert params["dateRange"] == "7d"
        assert params["aggInterval"] == "1h"

    await client.aclose()


async def test_initial_poll_timeout_falls_back_to_background(
    session_factory, monkeypatch
) -> None:
    """A hung initial poll must not block startup forever."""

    async def slow_fetch(*args, **kwargs):
        await asyncio.sleep(10.0)
        return None

    client = _make_client(_fixture_handler)
    monkeypatch.setattr(client, "fetch", slow_fetch)
    repo = ObservationRepository(session_factory)
    ingestor = RadarIngestor(
        client, repo, _settings(),
        initial_poll_timeout_seconds=0.05,
    )

    await ingestor.start()
    assert ingestor.last_success_at is None
    await ingestor.stop()

    await client.aclose()
