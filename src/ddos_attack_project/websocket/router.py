"""WebSocket endpoint for streaming real threat indicators and Radar pulses.

On connect the endpoint sends a small ``system`` welcome envelope so clients
get an immediate acknowledgement, followed by one ``radar_pulse`` carrying
the latest persisted 24h aggregates (when any exist) so a fresh client has
arcs immediately instead of waiting for the next heartbeat. Threat
indicators are then pushed as they land: broadcasts are produced by the
ThreatIntelIngestor (``threat_indicator``) and the RadarPulseBroadcaster
(``radar_pulse``) via the central ``ConnectionManager``.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ddos_attack_project.websocket.envelopes import SystemData, SystemMessage
from ddos_attack_project.websocket.manager import ConnectionManager
from ddos_attack_project.websocket.pulse import RadarPulseBroadcaster

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
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
