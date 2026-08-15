"""Synthetic geography: country lookup and in-country point pools.

Cloudflare Radar provides country codes and names, never coordinates. This
module generates representative synthetic points that fall inside each
country's bounding box so the globe does not show events originating from
arbitrary global coordinates.

These points are visual infrastructure. They are NOT attack telemetry and
are never presented as real attack locations.
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ddos_attack_project.domain.models import Country

_DATA_PATH: Final = Path(__file__).resolve().parent.parent / "data" / "countries.json"

#: Default number of synthetic points pooled per country (IMPLEMENTATION 14.1).
DEFAULT_POINTS_PER_COUNTRY: Final = 6


@dataclass(frozen=True)
class CountryGeometry:
    code: str
    name: str
    lat: float
    lng: float
    bounds: tuple[float, float, float, float]

    @property
    def min_lat(self) -> float:
        return self.bounds[0]

    @property
    def max_lat(self) -> float:
        return self.bounds[1]

    @property
    def min_lng(self) -> float:
        return self.bounds[2]

    @property
    def max_lng(self) -> float:
        return self.bounds[3]


@dataclass(frozen=True)
class SyntheticPoint:
    """A representative point inside a country's bounding box."""

    lat: float
    lng: float


class CountryCatalog:
    """Loads and looks up country geometry from the static data file."""

    def __init__(self, data_path: Path = _DATA_PATH) -> None:
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        self._countries: dict[str, CountryGeometry] = {}
        for code, entry in payload.items():
            bounds = entry["bounds"]
            self._countries[code] = CountryGeometry(
                code=code,
                name=entry["name"],
                lat=entry["lat"],
                lng=entry["lng"],
                bounds=(bounds[0], bounds[1], bounds[2], bounds[3]),
            )

    def has(self, code: str) -> bool:
        return code in self._countries

    def get(self, code: str) -> CountryGeometry:
        try:
            return self._countries[code]
        except KeyError:
            raise KeyError(f"unknown country code {code!r}") from None

    def country(self, code: str) -> Country:
        geometry = self.get(code)
        return Country(code=geometry.code, name=geometry.name)

    @property
    def codes(self) -> set[str]:
        return set(self._countries)


class CountryPointPool:
    """A small stable pool of synthetic points inside one country.

    The pool is generated once per country and reused across events so the
    globe shows density without creating hundreds of permanent points.
    """

    def __init__(
        self,
        geometry: CountryGeometry,
        *,
        size: int = DEFAULT_POINTS_PER_COUNTRY,
        seed: int | None = None,
    ) -> None:
        if size < 1:
            raise ValueError("point pool size must be >= 1")
        self.geometry = geometry
        self.size = size
        self._seed = seed if seed is not None else uuid.uuid4().int
        self._points: list[SyntheticPoint] | None = None

    def points(self) -> list[SyntheticPoint]:
        if self._points is None:
            self._points = self._generate()
        return self._points

    def _generate(self) -> list[SyntheticPoint]:
        rng = random.Random(self._seed)
        g = self.geometry
        points: list[SyntheticPoint] = []
        seen: set[tuple[float, float]] = set()
        while len(points) < self.size:
            lat = rng.uniform(g.min_lat, g.max_lat)
            lng = rng.uniform(g.min_lng, g.max_lng)
            key = (round(lat, 4), round(lng, 4))
            if key in seen:
                continue
            seen.add(key)
            points.append(SyntheticPoint(lat=lat, lng=lng))
        return points


class Geography:
    """Facade for the application's synthetic geography.

    ``pools_for`` is cached per (country, size) so repeated lookups reuse the
    same points across the whole process.
    """

    def __init__(
        self,
        catalog: CountryCatalog | None = None,
        *,
        points_per_country: int = DEFAULT_POINTS_PER_COUNTRY,
    ) -> None:
        self._catalog = catalog or CountryCatalog()
        self._points_per_country = points_per_country
        self._pools: dict[tuple[str, int], CountryPointPool] = {}

    @property
    def catalog(self) -> CountryCatalog:
        return self._catalog

    def pool_for(self, code: str, *, size: int | None = None) -> CountryPointPool:
        geometry = self._catalog.get(code)
        pool_size = size or self._points_per_country
        key = (code, pool_size)
        if key not in self._pools:
            self._pools[key] = CountryPointPool(geometry, size=pool_size)
        return self._pools[key]

    def random_point(self, code: str, rng: random.Random | None = None) -> SyntheticPoint:
        pool = self.pool_for(code)
        rng = rng or random.Random()
        return rng.choice(pool.points())
