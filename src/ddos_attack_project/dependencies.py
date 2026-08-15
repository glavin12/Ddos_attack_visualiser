"""FastAPI dependency injection helpers."""

from __future__ import annotations

from fastapi import Request

from ddos_attack_project.api.service import RadarQueryService


def get_radar_service(request: Request) -> RadarQueryService:
    """Return the app-scoped query service registered during lifespan."""
    service = getattr(request.app.state, "radar_service", None)
    if service is None:
        raise RuntimeError("radar_service is not initialized")
    return service
