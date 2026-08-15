from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSettings(BaseSettings):
    database_url: str = Field(
        validation_alias=AliasChoices(
            "DATABASE_URL",
            "SUPABASE_DATABASE_URL",
        )
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def asyncpg_url(self) -> str:
        """Return a SQLAlchemy URL configured for the asyncpg dialect."""
        url = make_url(self.database_url)

        if url.drivername in {"postgres", "postgresql"}:
            url = url.set(drivername="postgresql+asyncpg")

        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        if sslmode and sslmode != "disable" and "ssl" not in query:
            query["ssl"] = sslmode

        return url.set(query=query).render_as_string(hide_password=False)


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


def create_database_engine(
    settings: DatabaseSettings | None = None,
) -> AsyncEngine:
    resolved_settings = settings or get_database_settings()
    return create_async_engine(
        resolved_settings.asyncpg_url(),
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def check_database_connection(engine: AsyncEngine) -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    except SQLAlchemyError:
        return False
    return True
