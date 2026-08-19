"""Common types and helpers for threat-intel source adapters."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawIndicator:
    """One indicator as reported by a source, pre-geolocation.

    ``host`` is either an IP or a hostname; the ingestor resolves hostnames
    to IPs before geolocation.
    """

    indicator: str
    indicator_type: str
    host: str
    threat_family: str | None
    first_seen: datetime
    last_seen: datetime
    source_url: str | None


class SourceAdapter(Protocol):
    """The contract every threat-intel source adapter implements."""

    source_feed: str

    async def fetch(self) -> list[RawIndicator]: ...


def extract_host(indicator: str, indicator_type: str) -> str | None:
    """Return the host to geolocate for a raw indicator.

    IP-type indicators return themselves. URL/domain indicators return the
    parsed host. Returns ``None`` if extraction fails.
    """
    if indicator_type == "ip":
        return indicator
    if indicator_type == "domain":
        return indicator
    if indicator_type == "url":
        parsed = urlparse(indicator)
        return parsed.hostname
    return None


def is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


_DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def parse_feed_datetime(value: str | None) -> datetime | None:
    """Tolerant parser for the timestamp formats abuse.ch feeds actually use.

    Observed in practice (not guessed): URLhaus ``dateadded`` and ThreatFox
    ``first_seen``/``last_seen`` are ``"YYYY-MM-DD HH:MM:SS UTC"``; Feodo
    Tracker ``first_seen`` omits the suffix, and its ``last_online`` is
    date-only. A single strict ``strptime`` format silently drops every row
    the moment a feed's format doesn't match exactly, so this tries a small
    set of known shapes instead of one.
    """
    if not value:
        return None
    text = value.strip()
    if text.endswith(" UTC"):
        text = text[: -len(" UTC")]
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


async def resolve_hostname(host: str) -> str | None:
    """Resolve a hostname to an IP; returns ``None`` on failure.

    Uses ``asyncio.to_thread`` since ``socket.gethostbyname`` is blocking.
    """
    if not host:
        return None
    if is_ip_address(host):
        return host
    try:
        return await asyncio.to_thread(socket.gethostbyname, host)
    except (socket.gaierror, socket.herror, OSError):
        logger.debug("DNS resolution failed for %s", host)
        return None
