"""Cloudflare Radar endpoint registry and client.

The client is responsible for calling Cloudflare Radar, handling HTTP
errors, validating envelopes, and returning typed external response objects.
It must NOT normalize data, touch the database, or generate events.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from pydantic import TypeAdapter

from ddos_attack_project.domain.enums import EndpointKey
from ddos_attack_project.radar.external import (
    CloudflareEnvelope,
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
)


class RadarError(Exception):
    """Base error for Cloudflare Radar access."""


class RadarHTTPError(RadarError):
    """Raised when the Radar API returns a non-success HTTP status."""

    def __init__(self, status_code: int, detail: str | None = None) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Radar API HTTP {status_code}: {detail or ''}")


class RadarResponseError(RadarError):
    """Raised when the Radar API reports a failed envelope."""

    def __init__(self, errors: list[object] | None = None) -> None:
        self.errors = errors or []
        super().__init__(f"Radar API returned errors: {self.errors}")


@dataclass(frozen=True)
class RadarEndpoint:
    """Descriptor for one configured Radar endpoint."""

    key: EndpointKey
    path: str
    result_type: type[object]
    #: query parameters beyond the common ``dateRange``
    extra_query: dict[str, str] | None = None


_ENDPOINT_RESULTS = {
    CloudflareTopAttacksResult,
    CloudflareTopLocationsResult,
    CloudflareSummaryResult,
    CloudflareTimeSeriesResult,
}


def _adapter_for(result_type: type[object]) -> TypeAdapter[object]:
    return TypeAdapter(result_type)


ENDPOINTS: dict[EndpointKey, RadarEndpoint] = {
    EndpointKey.L3_TOP_ATTACKS: RadarEndpoint(
        key=EndpointKey.L3_TOP_ATTACKS,
        path="/attacks/layer3/top/attacks",
        result_type=CloudflareTopAttacksResult,
    ),
    EndpointKey.L7_TOP_ATTACKS: RadarEndpoint(
        key=EndpointKey.L7_TOP_ATTACKS,
        path="/attacks/layer7/top/attacks",
        result_type=CloudflareTopAttacksResult,
    ),
    EndpointKey.L3_TOP_ORIGIN: RadarEndpoint(
        key=EndpointKey.L3_TOP_ORIGIN,
        path="/attacks/layer3/top/locations/origin",
        result_type=CloudflareTopLocationsResult,
    ),
    EndpointKey.L3_TOP_TARGET: RadarEndpoint(
        key=EndpointKey.L3_TOP_TARGET,
        path="/attacks/layer3/top/locations/target",
        result_type=CloudflareTopLocationsResult,
    ),
    EndpointKey.L7_TOP_ORIGIN: RadarEndpoint(
        key=EndpointKey.L7_TOP_ORIGIN,
        path="/attacks/layer7/top/locations/origin",
        result_type=CloudflareTopLocationsResult,
    ),
    EndpointKey.L7_TOP_TARGET: RadarEndpoint(
        key=EndpointKey.L7_TOP_TARGET,
        path="/attacks/layer7/top/locations/target",
        result_type=CloudflareTopLocationsResult,
    ),
    EndpointKey.L3_SUMMARY_PROTOCOL: RadarEndpoint(
        key=EndpointKey.L3_SUMMARY_PROTOCOL,
        path="/attacks/layer3/summary/protocol",
        result_type=CloudflareSummaryResult,
    ),
    EndpointKey.L3_SUMMARY_VECTOR: RadarEndpoint(
        key=EndpointKey.L3_SUMMARY_VECTOR,
        path="/attacks/layer3/summary/vector",
        result_type=CloudflareSummaryResult,
    ),
    EndpointKey.L7_SUMMARY_HTTP_METHOD: RadarEndpoint(
        key=EndpointKey.L7_SUMMARY_HTTP_METHOD,
        path="/attacks/layer7/summary/http_method",
        result_type=CloudflareSummaryResult,
    ),
    EndpointKey.L3_TIMESERIES: RadarEndpoint(
        key=EndpointKey.L3_TIMESERIES,
        path="/attacks/layer3/timeseries",
        result_type=CloudflareTimeSeriesResult,
    ),
    EndpointKey.L7_TIMESERIES: RadarEndpoint(
        key=EndpointKey.L7_TIMESERIES,
        path="/attacks/layer7/timeseries",
        result_type=CloudflareTimeSeriesResult,
    ),
}


class RadarClient:
    """Async client for the Cloudflare Radar API."""

    def __init__(
        self,
        *,
        api_token: str,
        base_url: str = "https://api.cloudflare.com/client/v4/radar",
        timeout_seconds: float = 15.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http = http_client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
            },
        )
        self._owned_client = http_client is None

    async def fetch(
        self,
        endpoint: RadarEndpoint,
        *,
        date_range: str,
        limit: int | None = None,
        extra: dict[str, str] | None = None,
    ) -> object:
        """Fetch one endpoint and return its typed external result."""
        params: dict[str, str] = {"dateRange": date_range}
        if limit is not None:
            params["limit"] = str(limit)
        if endpoint.extra_query:
            params.update(endpoint.extra_query)
        if extra:
            params.update(extra)

        url = f"{self._base_url}{endpoint.path}"
        try:
            response = await self._http.get(url, params=params)
        except httpx.HTTPError as exc:
            raise RadarError(f"Radar request failed for {endpoint.path}") from exc

        if response.status_code != 200:
            raise RadarHTTPError(response.status_code, response.text[:500])

        try:
            payload = response.json()
        except ValueError as exc:
            raise RadarError("Radar returned non-JSON response") from exc

        envelope = CloudflareEnvelope.model_validate(payload)
        if not envelope.success:
            raise RadarResponseError(envelope.errors)

        return _adapter_for(endpoint.result_type).validate_python(envelope.result)

    async def aclose(self) -> None:
        if self._owned_client:
            await self._http.aclose()
