"""WebSocket endpoint for streaming real threat indicators and Radar pulses.

On connect the endpoint sends a small ``system`` welcome envelope so clients
get an immediate acknowledgement, followed by one ``radar_pulse`` carrying
the latest persisted 24h aggregates (when any exist) and a backlog of
recently-seen ``threat_indicator``s, so a fresh client sees arcs and dots
immediately instead of an empty globe until the next new IOC happens to
land. After that, both message types are pushed as they occur: broadcasts
are produced by the ThreatIntelIngestor (``threat_indicator``) and the
RadarPulseBroadcaster (``radar_pulse``) via the central ``ConnectionManager``.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ddos_attack_project.websocket.envelopes import (
    StatsData,
    StatsMessage,
    SystemData,
    SystemMessage,
    ThreatIndicatorData,
    ThreatIndicatorMessage,
)
from ddos_attack_project.websocket.manager import ConnectionManager
from ddos_attack_project.websocket.pulse import RadarPulseBroadcaster

_INDICATOR_BACKLOG_LIMIT = 200

router = APIRouter(prefix="/api/v1/ws")


@router.websocket("/radar")
async def radar_stream(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    await manager.send_to(
        websocket,
        SystemMessage(
            data=SystemData(message="Connected to Threat Observatory")
        ),
    )
    # Immediate latest-aggregates pulse — no-op until real Radar data exists
    # and skipped entirely when a no-op pulse broadcaster was injected (tests).
    pulse_broadcaster = getattr(
        websocket.app.state, "radar_pulse_broadcaster", None
    )
    if isinstance(pulse_broadcaster, RadarPulseBroadcaster):
        try:
            await pulse_broadcaster.send_to(websocket)
        except Exception:  # pragma: no cover - defensive; welcome already sent
            pass
    # Backlog of already-known indicators — without this, a fresh client only
    # ever sees dots for IOCs newly inserted *after* it connected, since
    # broadcast_threat_indicators only fires on new inserts.
    repository = getattr(
        websocket.app.state, "threat_indicator_repository", None
    )
    if repository is not None:
        try:
            recent = await repository.recent_indicators(
                limit=_INDICATOR_BACKLOG_LIMIT
            )
            for row in recent:
                if row.latitude is None or row.longitude is None:
                    continue
                await manager.send_to(
                    websocket,
                    ThreatIndicatorMessage(
                        data=ThreatIndicatorData.from_domain(row)
                    ),
                )
            await manager.send_to(
                websocket,
                StatsMessage(
                    data=StatsData(
                        active_indicators=await repository.count_active()
                    )
                ),
            )
        except Exception:  # pragma: no cover - defensive; welcome already sent
            pass
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
