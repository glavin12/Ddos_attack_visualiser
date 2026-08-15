from sqlalchemy.engine import make_url

from ddos_attack_project.database import DatabaseSettings


def test_database_settings_converts_postgresql_url_to_asyncpg() -> None:
    settings = DatabaseSettings(
        database_url=(
            "postgresql://user:password@example.test:5432/postgres"
            "?sslmode=require"
        )
    )

    asyncpg_url = make_url(settings.asyncpg_url())

    assert asyncpg_url.drivername == "postgresql+asyncpg"
    assert asyncpg_url.password == "password"
    assert asyncpg_url.query["ssl"] == "require"
    assert "sslmode" not in asyncpg_url.query
