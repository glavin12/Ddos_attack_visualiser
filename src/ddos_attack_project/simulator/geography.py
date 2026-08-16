"""Synthetic geography: country lookup and in-country city anchor points.

Cloudflare Radar provides country codes and names, never coordinates. This
module resolves every synthetic point to a real city inside the country so
the globe never shows events over ocean areas.

City coordinates come from a static dataset (GeoNames cities1000, top
``N`` cities per country by population). Each event picks a city weighted by
population, mirroring how real attack traffic geolocates to population
centers. Points are visual infrastructure — they are NOT attack telemetry
and are never presented as real attack locations.
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

from ddos_attack_project.domain.models import Country

_DATA_PATH: Final = Path(__file__).resolve().parent.parent / "data" / "countries.json"
_CITIES_PATH: Final = Path(__file__).resolve().parent.parent / "data" / "cities.json"

#: Default number of synthetic points pooled per country (IMPLEMENTATION 14.1).
DEFAULT_POINTS_PER_COUNTRY: Final = 6


@dataclass(frozen=True)
class City:
    """A real city used as an attack-point anchor."""

    name: str
    lat: float
    lng: float
    population: int


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
    """A representative point inside a country, anchored to a real city."""

    lat: float
    lng: float


class CountryCatalog:
    """Loads and looks up country geometry and city anchors."""

    def __init__(
        self,
        data_path: Path = _DATA_PATH,
        cities_path: Path = _CITIES_PATH,
    ) -> None:
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

        cities_payload = json.loads(cities_path.read_text(encoding="utf-8"))
        self._cities: dict[str, tuple[City, ...]] = {}
        for code, entries in cities_payload.items():
            if code not in self._countries:
                continue
            cities = [
                City(
                    name=entry["city"],
                    lat=float(entry["lat"]),
                    lng=float(entry["lng"]),
                    population=int(entry["population"]),
                )
                for entry in entries
            ]
            cities.sort(key=lambda c: c.population, reverse=True)
            self._cities[code] = tuple(cities)

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

    def cities(self, code: str) -> tuple[City, ...]:
        """Return the country's city anchors (population-desc)."""
        return self._cities.get(code, ())

    @property
    def codes(self) -> set[str]:
        return set(self._countries)


class CountryPointPool:
    """A stable pool of synthetic points inside one country.

    The pool is built from the country's top cities by population and reused
    across events so the globe shows density without creating hundreds of
    permanent points. Deterministic: derived from static data, so two pools
    for the same country are always identical.
    """

    def __init__(
        self,
        geometry: CountryGeometry,
        *,
        cities: Sequence[City] = (),
        size: int = DEFAULT_POINTS_PER_COUNTRY,
        seed: int | None = None,
    ) -> None:
        if size < 1:
            raise ValueError("point pool size must be >= 1")
        self.geometry = geometry
        self.size = size
        self._cities = tuple(cities)
        self._seed = seed if seed is not None else uuid.uuid4().int
        self._points: list[SyntheticPoint] | None = None

    def points(self) -> list[SyntheticPoint]:
        if self._points is None:
            self._points = self._generate()
        return self._points

    def _generate(self) -> list[SyntheticPoint]:
        if self._cities:
            return [
                SyntheticPoint(lat=city.lat, lng=city.lng)
                for city in self._cities[: self.size]
            ]
        # Fallback for countries without city data: the country centroid,
        # which lies on land by construction.
        return [SyntheticPoint(lat=self.geometry.lat, lng=self.geometry.lng)]


class Geography:
    """Facade for the application's synthetic geography.

    ``random_point`` picks a real city per country weighted by population.
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
            self._pools[key] = CountryPointPool(
                geometry,
                cities=self._catalog.cities(code),
                size=pool_size,
            )
        return self._pools[key]

    def random_point(self, code: str, rng: random.Random | None = None) -> SyntheticPoint:
        """Pick a city anchor inside the country, weighted by population."""
        rng = rng or random.Random()
        cities = self._catalog.cities(code)
        if cities:
            weights = [max(1, city.population) for city in cities]
            city = rng.choices(cities, weights=weights, k=1)[0]
            return SyntheticPoint(lat=city.lat, lng=city.lng)
        return self.pool_for(code).points()[0]
