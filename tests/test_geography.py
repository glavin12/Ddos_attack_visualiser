"""Tests for synthetic geography."""

from __future__ import annotations

import random

import pytest

from ddos_attack_project.simulator.geography import (
    CountryCatalog,
    CountryPointPool,
    Geography,
    SyntheticPoint,
)


@pytest.fixture(scope="module")
def catalog() -> CountryCatalog:
    return CountryCatalog()


def test_catalog_covers_fixture_codes(catalog: CountryCatalog) -> None:
    from tests.conftest import FIXTURES
    import json

    codes: set[str] = set()
    for path in FIXTURES.glob("*top*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data.get("result", {}).get("top_0", []):
            codes.add(record.get("originCountryAlpha2") or record.get("targetCountryAlpha2"))
    assert codes <= catalog.codes


def test_catalog_get(catalog: CountryCatalog) -> None:
    geometry = catalog.get("US")
    assert geometry.code == "US"
    assert geometry.name == "United States"
    assert -124.8 <= geometry.lng <= -66.9


def test_catalog_unknown_code(catalog: CountryCatalog) -> None:
    with pytest.raises(KeyError):
        catalog.get("ZZ")


def test_catalog_country_domain_object(catalog: CountryCatalog) -> None:
    country = catalog.country("IN")
    assert country.code == "IN"
    assert country.name == "India"


def test_point_pool_points_inside_bounds(catalog: CountryCatalog) -> None:
    geometry = catalog.get("BR")
    pool = CountryPointPool(geometry, size=8)
    for point in pool.points():
        assert geometry.min_lat <= point.lat <= geometry.max_lat
        assert geometry.min_lng <= point.lng <= geometry.max_lng


def test_point_pool_size_and_uniqueness(catalog: CountryCatalog) -> None:
    pool = CountryPointPool(catalog.get("US"), size=6)
    points = pool.points()
    assert len(points) == 6
    assert len({(p.lat, p.lng) for p in points}) == 6


def test_point_pool_stable_with_seed(catalog: CountryCatalog) -> None:
    first = CountryPointPool(catalog.get("US"), size=6, seed=42).points()
    second = CountryPointPool(catalog.get("US"), size=6, seed=42).points()
    assert first == second


def test_point_pool_reuse_same_object(catalog: CountryCatalog) -> None:
    pool = CountryPointPool(catalog.get("DE"), size=6)
    assert pool.points() is pool.points()


def test_point_pool_rejects_zero_size(catalog: CountryCatalog) -> None:
    with pytest.raises(ValueError):
        CountryPointPool(catalog.get("US"), size=0)


def test_geography_pool_cached(catalog: CountryCatalog) -> None:
    geo = Geography(catalog)
    assert geo.pool_for("FR") is geo.pool_for("FR")
    assert geo.pool_for("FR") is not geo.pool_for("DE")


def test_geography_random_point_inside_country(catalog: CountryCatalog) -> None:
    geo = Geography(catalog)
    point = geo.random_point("AU", rng=random.Random(7))
    geometry = catalog.get("AU")
    assert geometry.min_lat <= point.lat <= geometry.max_lat
    assert geometry.min_lng <= point.lng <= geometry.max_lng
    assert isinstance(point, SyntheticPoint)


def test_geography_reuses_pool_across_random_points(
    catalog: CountryCatalog,
) -> None:
    geo = Geography(catalog)
    rng = random.Random(1)
    points = {geo.random_point("IN", rng=rng) for _ in range(20)}
    assert len(points) <= 6
