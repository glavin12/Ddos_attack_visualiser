"""abuse.ch Feodo Tracker adapter — active botnet C2 IPs, no key required."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from ddos_attack_project.threatintel.sources.base import RawIndicator

logger = logging.getLogger(__name__)

_FEED_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


class FeodoAdapter:
    source_feed = "feodo"

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
            logger.exception("Feodo Tracker fetch failed")
            return []
        if response.status_code != 200:
            logger.warning(
                "Feodo Tracker returned HTTP %s", response.status_code
            )
            return []
        try:
            payload = response.json()
        except ValueError:
            logger.warning("Feodo Tracker returned non-JSON")
            return []
        if not isinstance(payload, list):
            return []
        return list(self._parse(payload))

    async def aclose(self) -> None:
        if self._owned_client:
            await self._http.aclose()

    def _parse(self, payload: list) -> list[RawIndicator]:
        results: list[RawIndicator] = []
        for entry in payload:
            try:
                ip = entry["ip_address"]
                first_seen = _parse_datetime(entry.get("first_seen"))
                last_seen = _parse_datetime(
                    entry.get("last_online") or entry.get("first_seen")
                )
                if first_seen is None or last_seen is None:
                    continue
                malware = entry.get("malware") or None
                results.append(
                    RawIndicator(
                        indicator=ip,
                        indicator_type="ip",
                        host=ip,
                        threat_family=malware,
                        first_seen=first_seen,
                        last_seen=last_seen,
                        source_url=f"https://feodotracker.abuse.ch/browse/host/{ip}/",
                    )
                )
            except (KeyError, TypeError):
                continue
            if len(results) >= self._max_indicators:
                break
        return results


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _DATE_FMT).replace(tzinfo=UTC)
    except ValueError:
        return None
