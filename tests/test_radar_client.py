"""Tests for the Cloudflare Radar client."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from ddos_attack_project.domain.enums import EndpointKey
from ddos_attack_project.radar.client import (
    ENDPOINTS,
    RadarClient,
    RadarError,
    RadarHTTPError,
    RadarResponseError,
)

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "radar"


def load_fixture(name: str) -> bytes:
    path = FIXTURES / f"{name}.json"
    assert path.exists(), f"missing fixture {path}"
    return path.read_bytes()


def make_client(handler) -> RadarClient:
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


async def test_fetch_returns_typed_result() -> None:
    body = load_fixture("layer3-top-attacks")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-token"
        assert "dateRange=1d" in str(request.url)
        assert "limit=100" in str(request.url)
        return httpx.Response(200, content=body)

    client = make_client(handler)
    result = await client.fetch(
        ENDPOINTS[EndpointKey.L3_TOP_ATTACKS],
        date_range="1d",
        limit=100,
    )
    assert isinstance(result, object)
    assert getattr(result, "top_0", None) is not None


async def test_fetch_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = make_client(handler)
    with pytest.raises(RadarHTTPError) as exc_info:
        await client.fetch(
            ENDPOINTS[EndpointKey.L3_TOP_ATTACKS], date_range="1d"
        )
    assert exc_info.value.status_code == 500


async def test_fetch_envelope_success_false() -> None:
    payload = {
        "success": False,
        "errors": [{"code": 2001, "message": "Invalid Date Range"}],
        "result": {},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=json.dumps(payload).encode("utf-8")
        )

    client = make_client(handler)
    with pytest.raises(RadarResponseError) as exc_info:
        await client.fetch(
            ENDPOINTS[EndpointKey.L3_TOP_ATTACKS], date_range="1d"
        )
    assert exc_info.value.errors[0]["code"] == 2001


async def test_fetch_non_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    client = make_client(handler)
    with pytest.raises(RadarError):
        await client.fetch(
            ENDPOINTS[EndpointKey.L3_TOP_ATTACKS], date_range="1d"
        )


async def test_all_endpoints_registered() -> None:
    assert set(ENDPOINTS) == set(EndpointKey)
    assert len(ENDPOINTS) == 11


async def test_aclose_disposes_owned_client() -> None:
    client = RadarClient(api_token="test-token")
    await client.aclose()
