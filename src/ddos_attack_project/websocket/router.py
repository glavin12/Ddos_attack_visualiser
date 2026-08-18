"""WebSocket endpoint for streaming real threat indicators.

On connect the endpoint sends a small ``system`` welcome envelope so clients
get an immediate acknowledgement, then keeps the connection open for the
lifetime of the client. Broadcasts are produced by the ThreatIntelIngestor
via the central ``ConnectionManager``.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ddos_attack_project.websocket.envelopes import SystemData, SystemMessage
from ddos_attack_project.websocket.manager import ConnectionManager

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
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
