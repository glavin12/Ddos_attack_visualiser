"""Live-database integration tests for the normalized schema.

These tests run only when ``RUN_DATABASE_TESTS=1`` is set. They connect to the
configured Supabase database and verify the normalized schema behaves as
expected.
"""

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ddos_attack_project.database import (
    create_database_engine,
    get_database_settings,
)


pytestmark = pytest.mark.asyncio

NORMALIZED_TABLES = [
    "radar_observations",
    "attack_pairs",
    "country_distributions",
    "attack_characteristics",
    "timeseries_points",
]


@pytest_asyncio.fixture
async def database_engine():
    if os.getenv("RUN_DATABASE_TESTS") != "1":
        pytest.skip("Set RUN_DATABASE_TESTS=1 to run database integration tests")

    engine = create_database_engine(get_database_settings())
    yield engine
    await engine.dispose()


async def test_schema_crud_with_foreign_keys(database_engine) -> None:
    observation_id = str(uuid4())
    pair_id = str(uuid4())
    observed_at = datetime.now(UTC)

    async with database_engine.connect() as connection:
        try:
            extension = await connection.scalar(
                text(
                    "select exists("  # noqa: E501
                    "select 1 from pg_extension where extname = 'pgcrypto'"
                    ")"
                )
            )
            assert extension is True

            await connection.execute(
                text(
                    "insert into public.radar_observations "
                    "(id, refresh_id, endpoint_key, layer, collected_at, "
                    "window_start, window_end, cloudflare_last_updated, "
                    "normalization, unit) values "
                    "(:id, :refresh_id, 'layer3-top-attacks', 'L3', "
                    ":collected_at, :window_start, :window_end, "
                    ":last_updated, 'PERCENTAGE', 'bytes')"
                ),
                {
                    "id": observation_id,
                    "refresh_id": str(uuid4()),
                    "collected_at": observed_at,
                    "window_start": observed_at,
                    "window_end": observed_at,
                    "last_updated": observed_at,
                },
            )
            await connection.execute(
                text(
                    "insert into public.attack_pairs "
                    "(id, observation_id, layer, source_country_code, "
                    "source_country_name, target_country_code, "
                    "target_country_name, share, rank, unit) values "
                    "(:id, :observation_id, 'L3', 'BR', 'Brazil', 'US', "
                    "'United States', 0.06844203, NULL, 'bytes')"
                ),
                {"id": pair_id, "observation_id": observation_id},
            )

            layer = await connection.scalar(
                text(
                    "select layer from public.radar_observations "
                    "where id = :id"
                ),
                {"id": observation_id},
            )
            pair_source = await connection.scalar(
                text(
                    "select source_country_code from public.attack_pairs "
                    "where id = :id"
                ),
                {"id": pair_id},
            )

            assert layer == "L3"
            assert pair_source == "BR"
        finally:
            await connection.rollback()


async def test_attack_snapshots_retired(database_engine) -> None:
    async with database_engine.connect() as connection:
        exists = await connection.scalar(
            text(
                "select exists("  # noqa: E501
                "select 1 from information_schema.tables "
                "where table_schema = 'public' "
                "and table_name = 'attack_snapshots'"
                ")"
            )
        )
        assert exists is False


async def test_security_indexes_and_constraints(database_engine) -> None:
    async with database_engine.connect() as connection:
        row_security = set(
            await connection.scalars(
                text(
                    "select c.relname "
                    "from pg_class c "
                    "join pg_namespace n on n.oid = c.relnamespace "
                    "where n.nspname = 'public' "
                    f"and c.relname in ({_table_list()}) "
                    "and c.relrowsecurity"
                )
            )
        )
        assert row_security == set(NORMALIZED_TABLES)

        indexes = set(
            await connection.scalars(
                text(
                    "select indexname from pg_indexes "
                    "where schemaname = 'public' "
                    f"and tablename in ({_table_list()})"
                )
            )
        )
        assert {
            "idx_radar_observations_refresh_id",
            "idx_radar_observations_layer_collected_at",
            "idx_attack_pairs_observation_id",
            "idx_country_distributions_observation_id",
            "idx_attack_characteristics_observation_id",
            "idx_timeseries_points_observation_id",
        } <= indexes

        policy_count = await connection.scalar(
            text(
                "select count(*) from pg_policies "
                "where schemaname = 'public' "
                f"and tablename in ({_table_list()})"
            )
        )
        assert policy_count == 0

        # Constraint checks on radar_observations.
        observation_columns = (
            "id, refresh_id, endpoint_key, layer, collected_at, "
            "normalization, unit"
        )
        valid_observation = (
            "gen_random_uuid(), gen_random_uuid(), 'layer3-top-attacks', "
            "'L3', now(), 'PERCENTAGE', 'bytes'"
        )
        invalid_observations = [
            valid_observation.replace("'L3'", "'L4'"),
            valid_observation.replace("'PERCENTAGE'", "'OTHER'"),
            valid_observation.replace("'bytes'", "'packets'"),
        ]
        for values in invalid_observations:
            try:
                async with connection.begin_nested():
                    await connection.execute(
                        text(
                            "insert into public.radar_observations "
                            f"({observation_columns}) values ({values})"
                        )
                    )
            except IntegrityError:
                continue
            pytest.fail(f"Invalid observation accepted: {values}")

        # Constraint checks on attack_pairs. Use a real observation so FK
        # violations do not mask the specific checks under test.
        observation_id = await connection.scalar(
            text(
                "insert into public.radar_observations "
                "(id, refresh_id, endpoint_key, layer, collected_at, "
                "normalization, unit) values "
                "(gen_random_uuid(), gen_random_uuid(), "
                "'layer3-top-attacks', 'L3', now(), 'PERCENTAGE', 'bytes') "
                "returning id"
            )
        )
        pair_columns = (
            "id, observation_id, layer, source_country_code, "
            "target_country_code, share, unit"
        )
        pair_base = (
            f"gen_random_uuid(), '{observation_id}', 'L3', 'RU', 'US', "
            "0.1, 'bytes'"
        )
        invalid_pairs = [
            pair_base.replace("'L3'", "'L4'"),  # bad layer
            pair_base.replace("'RU'", "'ru'"),  # lowercase country
            pair_base.replace("0.1", "1.1"),  # share > 1
            pair_base.replace("'RU'", "'T1'"),  # Tor code must be allowed
        ]
        for values in invalid_pairs[:-1]:
            try:
                async with connection.begin_nested():
                    await connection.execute(
                        text(
                            "insert into public.attack_pairs "
                            f"({pair_columns}) values ({values})"
                        )
                    )
            except IntegrityError:
                continue
            pytest.fail(f"Invalid attack pair accepted: {values}")

        # Tor code 'T1' must be accepted.
        async with connection.begin_nested():
            await connection.execute(
                text(
                    "insert into public.attack_pairs "
                    f"({pair_columns}) values ({invalid_pairs[-1]})"
                )
            )


def _table_list() -> str:
    return ", ".join(f"'{name}'" for name in NORMALIZED_TABLES)
