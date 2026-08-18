"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

logger = logging.getLogger(__name__)

from ddos_attack_project.api.router import router as api_router
from ddos_attack_project.api.service import RadarQueryService
from ddos_attack_project.config import AppSettings, get_settings
from ddos_attack_project.database import (
    create_database_engine,
    create_session_factory,
)
from ddos_attack_project.db.repositories import (
    ObservationRepository,
    ThreatIndicatorRepository,
)
from ddos_attack_project.radar.client import RadarClient
from ddos_attack_project.radar.ingestor import RadarIngestor
from ddos_attack_project.threatintel.enrichment import GreyNoiseEnricher
from ddos_attack_project.threatintel.geoip import GeoIPService
from ddos_attack_project.threatintel.ingestor import ThreatIntelIngestor
from ddos_attack_project.threatintel.sources.feodo import FeodoAdapter
from ddos_attack_project.threatintel.sources.threatfox import ThreatFoxAdapter
from ddos_attack_project.threatintel.sources.urlhaus import URLhausAdapter
from ddos_attack_project.websocket.manager import ConnectionManager
from ddos_attack_project.websocket.router import router as ws_router


class IngestorLike(Protocol):
    """Minimal shape the app uses from an ingestor (for test injection)."""

    async def start(self) -> None: ...
    async def stop(self) -> None: ...


def create_app(
    settings: AppSettings | None = None,
    *,
    session_factory: async_sessionmaker | None = None,
    engine: AsyncEngine | None = None,
    stale_after_seconds: int | None = None,
    ingestor: IngestorLike | None = None,
    threatintel_ingestor: IngestorLike | None = None,
) -> FastAPI:
    """Build the FastAPI application.

    ``session_factory``, ``engine``, ``ingestor``, and ``threatintel_ingestor``
    are injectable for tests; by default they are derived from the configured
    database URL and disposed on shutdown. Pass no-op ingestors in tests to
    skip real HTTP traffic to Cloudflare and abuse.ch.
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
    injected_ingestor = ingestor
    injected_threatintel = threatintel_ingestor

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository = ObservationRepository(resolved_session_factory)
        threat_repository = ThreatIndicatorRepository(resolved_session_factory)
        app.state.radar_service = RadarQueryService(
            repository,
            stale_after_seconds=resolved_stale_after,
        )
        app.state.threat_indicator_repository = threat_repository
        manager = ConnectionManager()
        app.state.ws_manager = manager

        # --- Radar ingestor ---
        if injected_ingestor is not None:
            radar_client: RadarClient | None = None
            active_ingestor: IngestorLike = injected_ingestor
        else:
            radar_client = RadarClient(
                api_token=resolved_settings.cf_api_token,
                base_url=resolved_settings.radar_base_url,
                timeout_seconds=resolved_settings.radar_timeout_seconds,
            )
            active_ingestor = RadarIngestor(
                radar_client, repository, resolved_settings
            )
        app.state.radar_ingestor = active_ingestor
        await active_ingestor.start()

        # --- Threat-intel ingestor ---
        threatintel_owned: list = []
        if injected_threatintel is not None:
            active_threatintel: IngestorLike = injected_threatintel
        else:
            urlhaus = URLhausAdapter(
                timeout_seconds=resolved_settings.threatintel_http_timeout_seconds,
                max_indicators=resolved_settings.threatintel_max_indicators_per_feed,
            )
            feodo = FeodoAdapter(
                timeout_seconds=resolved_settings.threatintel_http_timeout_seconds,
                max_indicators=resolved_settings.threatintel_max_indicators_per_feed,
            )
            threatfox = ThreatFoxAdapter(
                api_key=resolved_settings.threat_fox_auth,
                timeout_seconds=resolved_settings.threatintel_http_timeout_seconds,
                max_indicators=resolved_settings.threatintel_max_indicators_per_feed,
            )
            geoip = GeoIPService(resolved_settings.maxmind_city_db_path)
            greynoise = GreyNoiseEnricher(
                resolved_settings.greynoise_comm_key,
                timeout_seconds=resolved_settings.threatintel_http_timeout_seconds,
            )
            threatintel_owned = [urlhaus, feodo, threatfox, greynoise, geoip]
            active_threatintel = ThreatIntelIngestor(
                settings=resolved_settings,
                repository=threat_repository,
                adapters=[urlhaus, feodo, threatfox],
                geoip=geoip,
                greynoise=greynoise,
                on_new_indicators=manager.broadcast_threat_indicators,
            )
        app.state.threatintel_ingestor = active_threatintel
        await active_threatintel.start()

        try:
            yield
        finally:
            await active_threatintel.stop()
            for owned in threatintel_owned:
                closer = getattr(owned, "aclose", None) or getattr(
                    owned, "close", None
                )
                if closer is None:
                    continue
                try:
                    result = closer()
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass
            await active_ingestor.stop()
            if radar_client is not None:
                await radar_client.aclose()
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

    @app.exception_handler(SQLAlchemyError)
    async def _sqlalchemy_error_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Turn database failures into a distinct 503 the frontend can act on.

        Frontend contract:
        - 200 with empty entries + null observation.collected_at = "no data yet"
        - 503 with body.status = "backend_error" = "something is broken"
        """
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=503,
            content={
                "status": "backend_error",
                "detail": "The data store is currently unreachable.",
            },
        )

    app.include_router(api_router)
    app.include_router(ws_router)
    return app


# Default application instance for standard `uvicorn ddos_attack_project.main:app`
app = create_app()
