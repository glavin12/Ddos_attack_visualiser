"""abuse.ch URLhaus adapter — recent malicious URLs, no API key required."""

from __future__ import annotations

import logging

import httpx

from ddos_attack_project.threatintel.sources.base import (
    RawIndicator,
    extract_host,
    parse_feed_datetime,
)

logger = logging.getLogger(__name__)

_FEED_URL = "https://urlhaus.abuse.ch/downloads/json_recent/"


class URLhausAdapter:
    source_feed = "urlhaus"

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 20.0,
        max_indicators: int = 200,
    ) -> None:
        self._http = http_client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )
        self._owned_client = http_client is None
        self._max_indicators = max_indicators

    async def fetch(self) -> list[RawIndicator]:
        try:
            response = await self._http.get(_FEED_URL)
        except httpx.HTTPError:
            logger.exception("URLhaus fetch failed")
            return []
        if response.status_code != 200:
            logger.warning("URLhaus returned HTTP %s", response.status_code)
            return []
        try:
            payload = response.json()
        except ValueError:
            logger.warning("URLhaus returned non-JSON")
            return []
        return list(self._parse(payload))

    async def aclose(self) -> None:
        if self._owned_client:
            await self._http.aclose()

    def _parse(self, payload: dict) -> list[RawIndicator]:
        results: list[RawIndicator] = []
        # URLhaus JSON: {"<id>": [{fields...}]} — one-element list per key.
        for entries in payload.values():
            if not entries:
                continue
            entry = entries[0] if isinstance(entries, list) else entries
            try:
                indicator = entry["url"]
                host = extract_host(indicator, "url") or ""
                threat = entry.get("threat") or entry.get("tags") or None
                if isinstance(threat, list):
                    threat = ", ".join(threat) or None
                first_seen = parse_feed_datetime(entry.get("dateadded"))
                if first_seen is None:
                    continue
                results.append(
                    RawIndicator(
                        indicator=indicator,
                        indicator_type="url",
                        host=host,
                        threat_family=threat,
                        first_seen=first_seen,
                        last_seen=first_seen,
                        source_url=entry.get("urlhaus_link"),
                    )
                )
            except (KeyError, TypeError):
                continue
            if len(results) >= self._max_indicators:
                break
        return results
