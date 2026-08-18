"""MaxMind GeoLite2 city lookup wrapper.

Uses a local ``.mmdb`` file (downloaded by the user via their MaxMind
license key). If the file is missing or unreadable, lookups return ``None``
gracefully — indicators are still persisted, just without geolocation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeoLocation:
    """A resolved geolocation for an IP address."""

    country_code: str | None
    country_name: str | None
    city: str | None
    latitude: float | None
    longitude: float | None


class GeoIPService:
    """Thin wrapper over ``maxminddb`` that never raises on lookup errors."""

    def __init__(self, db_path: str | Path | None) -> None:
        self._db_path = Path(db_path) if db_path else None
        self._reader: Any = None
        self._open_attempted = False

    def _ensure_open(self) -> None:
        if self._open_attempted:
            return
        self._open_attempted = True
        if self._db_path is None or not self._db_path.exists():
            logger.warning(
                "MaxMind GeoLite2 DB not found at %s; geolocation disabled",
                self._db_path,
            )
            return
        try:
            import maxminddb

            self._reader = maxminddb.open_database(str(self._db_path))
            logger.info("MaxMind GeoLite2 DB opened at %s", self._db_path)
        except Exception:
            logger.exception(
                "Failed to open MaxMind GeoLite2 DB at %s", self._db_path
            )
            self._reader = None

    def lookup(self, ip: str) -> GeoLocation | None:
        """Look up a single IP; return ``None`` on any failure."""
        self._ensure_open()
        if self._reader is None or not ip:
            return None
        try:
            record = self._reader.get(ip)
        except Exception:
            logger.debug("GeoIP lookup failed for %s", ip, exc_info=True)
            return None
        if not record:
            return None

        country = record.get("country") or {}
        city = record.get("city") or {}
        location = record.get("location") or {}

        return GeoLocation(
            country_code=country.get("iso_code"),
            country_name=(country.get("names") or {}).get("en"),
            city=(city.get("names") or {}).get("en"),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        )

    def close(self) -> None:
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass
            self._reader = None
