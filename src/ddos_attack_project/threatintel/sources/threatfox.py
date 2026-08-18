"""abuse.ch ThreatFox adapter — fresh IOCs tagged by malware family.

Requires the free ``THREAT_FOX_AUTH`` key sent as an ``Auth-Key`` header.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from ddos_attack_project.threatintel.sources.base import RawIndicator, is_ip_address

logger = logging.getLogger(__name__)

_API_URL = "https://threatfox-api.abuse.ch/api/v1/"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


class ThreatFoxAdapter:
    source_feed = "threatfox"

    def __init__(
        self,
        api_key: str | None,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 20.0,
        max_indicators: int = 200,
        days: int = 1,
    ) -> None:
        self._api_key = api_key
        self._http = http_client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )
        self._owned_client = http_client is None
        self._max_indicators = max_indicators
        self._days = days

    async def fetch(self) -> list[RawIndicator]:
        if not self._api_key:
            logger.info(
                "ThreatFox key not configured; skipping fetch"
            )
            return []
        try:
            response = await self._http.post(
                _API_URL,
                headers={"Auth-Key": self._api_key},
                json={"query": "get_iocs", "days": self._days},
            )
        except httpx.HTTPError:
            logger.exception("ThreatFox fetch failed")
            return []
        if response.status_code != 200:
            logger.warning("ThreatFox returned HTTP %s", response.status_code)
            return []
        try:
            payload = response.json()
        except ValueError:
            return []
        if payload.get("query_status") != "ok":
            logger.warning(
                "ThreatFox query_status=%s", payload.get("query_status")
            )
            return []
        return list(self._parse(payload.get("data") or []))

    async def aclose(self) -> None:
        if self._owned_client:
            await self._http.aclose()

    def _parse(self, data: list) -> list[RawIndicator]:
        results: list[RawIndicator] = []
        for entry in data:
            try:
                ioc = entry.get("ioc")
                if not ioc:
                    continue
                ioc_type_raw = entry.get("ioc_type") or ""
                indicator_type = _classify(ioc_type_raw, ioc)
                if indicator_type is None:
                    continue
                host = _extract_host(indicator_type, ioc)
                if not host:
                    continue
                first_seen = _parse_datetime(entry.get("first_seen"))
                last_seen = _parse_datetime(
                    entry.get("last_seen") or entry.get("first_seen")
                )
                if first_seen is None or last_seen is None:
                    continue
                malware = entry.get("malware_printable") or entry.get("malware") or None
                source_url = None
                if entry.get("id"):
                    source_url = f"https://threatfox.abuse.ch/ioc/{entry['id']}/"
                results.append(
                    RawIndicator(
                        indicator=ioc,
                        indicator_type=indicator_type,
                        host=host,
                        threat_family=malware,
                        first_seen=first_seen,
                        last_seen=last_seen,
                        source_url=source_url,
                    )
                )
            except (KeyError, TypeError):
                continue
            if len(results) >= self._max_indicators:
                break
        return results


def _classify(ioc_type_raw: str, ioc: str) -> str | None:
    lower = ioc_type_raw.lower()
    if "ip" in lower:
        # Some ThreatFox IPs come as "ip:port" — strip the port.
        return "ip"
    if "url" in lower:
        return "url"
    if "domain" in lower:
        return "domain"
    # Fallback: infer from the ioc itself.
    if is_ip_address(ioc.split(":")[0]):
        return "ip"
    return None


def _extract_host(indicator_type: str, ioc: str) -> str | None:
    if indicator_type == "ip":
        return ioc.split(":")[0]
    if indicator_type == "domain":
        return ioc
    if indicator_type == "url":
        from urllib.parse import urlparse

        return urlparse(ioc).hostname
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, _DATE_FMT).replace(tzinfo=UTC)
    except ValueError:
        return None
