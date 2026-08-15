"""WebSocket endpoint for streaming synthetic visualization events.

The connection is kept open for the client lifetime. The scheduler (owned by
the application) broadcasts attack/stats/system messages through the central
``ConnectionManager``; this endpoint only accepts connections and waits.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ddos_attack_project.websocket.manager import ConnectionManager

router = APIRouter(prefix="/api/v1/ws")


@router.websocket("/radar")
async def radar_stream(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
