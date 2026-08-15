"""FastAPI application factory."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from ddos_attack_project.api.router import router as api_router
from ddos_attack_project.api.service import RadarQueryService
from ddos_attack_project.config import AppSettings, get_settings
from ddos_attack_project.database import (
    create_database_engine,
    create_session_factory,
)
from ddos_attack_project.db.repositories import ObservationRepository
from ddos_attack_project.simulator.runtime import SimulationRuntime
from ddos_attack_project.websocket.manager import ConnectionManager
from ddos_attack_project.websocket.router import router as ws_router


def create_app(
    settings: AppSettings | None = None,
    *,
    session_factory: async_sessionmaker | None = None,
    engine: AsyncEngine | None = None,
    stale_after_seconds: int | None = None,
) -> FastAPI:
    """Build the FastAPI application.

    ``session_factory`` and ``engine`` are injectable for tests; by default
    they are derived from the configured database URL and disposed on
    shutdown.
    """
    resolved_settings = settings or get_settings()

    owned_engine = engine is None
    resolved_engine = engine or create_database_engine()
    resolved_session_factory = session_factory or create_session_factory(
        resolved_engine
    )
    resolved_stale_after = (
        stale_after_seconds or resolved_settings.radar_refresh_seconds * 2
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = ObservationRepository(resolved_session_factory)
        app.state.radar_service = RadarQueryService(
            repository,
            stale_after_seconds=resolved_stale_after,
        )
        manager = ConnectionManager()
        app.state.ws_manager = manager
        runtime = SimulationRuntime(repository, manager, resolved_settings)
        app.state.simulation_runtime = runtime
        await runtime.start()
        try:
            yield
        finally:
            await runtime.stop()
            if owned_engine:
                await resolved_engine.dispose()

    app = FastAPI(
        title="DDoS Attack Visualizer API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.include_router(ws_router)
    return app
