"""WebSocket API - Real-time production status streaming."""

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])

# Track connected clients per project
_connections: dict[str, list[WebSocket]] = {}


async def broadcast_to_project(project_id: str, message: dict):
    """Broadcast a message to all connected clients for a project."""
    if project_id in _connections:
        disconnected = []
        for ws in _connections[project_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            _connections[project_id].remove(ws)


@router.websocket("/ws/v1/production/{project_id}")
async def production_websocket(websocket: WebSocket, project_id: UUID):
    """WebSocket endpoint for real-time render progress and production status."""
    pid = str(project_id)
    
    await websocket.accept()
    
    if pid not in _connections:
        _connections[pid] = []
    _connections[pid].append(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "project_id": pid,
            "message": "Connected to production stream",
        })
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            # Echo back with status
            await websocket.send_json({
                "type": "ack",
                "received": msg.get("type", "unknown"),
            })
    
    except WebSocketDisconnect:
        _connections[pid].remove(websocket)
        if not _connections[pid]:
            del _connections[pid]