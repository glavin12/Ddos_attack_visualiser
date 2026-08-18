"""GreyNoise Community API enrichment for threat indicators.

The Community endpoint (free 10k/day) returns whether an IP is a known
scanner and a short classification/tag. We enrich only the top-N newest
indicators per poll cycle to stay within the quota.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_COMMUNITY_URL = "https://api.greynoise.io/v3/community/{ip}"


@dataclass(frozen=True)
class GreyNoiseInfo:
    classification: str | None
    tags: str | None


class GreyNoiseEnricher:
    """Lookup individual IPs against GreyNoise Community.

    Missing key → no-op (every lookup returns ``None``). This is intentional
    so the ingest pipeline still works without a GreyNoise account.
    """

    def __init__(
        self,
        api_key: str | None,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._api_key = api_key
        self._http = http_client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )
        self._owned_client = http_client is None

    async def lookup(self, ip: str) -> GreyNoiseInfo | None:
        if not self._api_key or not ip:
            return None
        try:
            response = await self._http.get(
                _COMMUNITY_URL.format(ip=ip),
                headers={"key": self._api_key},
            )
        except httpx.HTTPError:
            logger.debug("GreyNoise lookup failed for %s", ip, exc_info=True)
            return None
        if response.status_code == 404:
            return GreyNoiseInfo(classification="unseen", tags=None)
        if response.status_code != 200:
            return None
        try:
            payload = response.json()
        except ValueError:
            return None
        return GreyNoiseInfo(
            classification=payload.get("classification"),
            tags=", ".join(payload["tags"]) if payload.get("tags") else None,
        )

    async def aclose(self) -> None:
        if self._owned_client:
            await self._http.aclose()
