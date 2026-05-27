from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import json
import asyncio

from forge.configs.settings import settings

router = APIRouter()

# In-memory connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, experiment_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(experiment_id, []).append(websocket)

    def disconnect(self, experiment_id: str, websocket: WebSocket):
        conns = self.active_connections.get(experiment_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(experiment_id, None)

    async def broadcast(self, experiment_id: str, message: dict):
        conns = self.active_connections.get(experiment_id, [])
        if not conns:
            return
        payload = json.dumps(message, default=str)
        dead = []
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(experiment_id, ws)

manager = ConnectionManager()


@router.websocket("/api/v1/experiments/{experiment_id}/ws")
async def experiment_websocket(experiment_id: str, websocket: WebSocket):
    await manager.connect(experiment_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(experiment_id, websocket)
    except Exception:
        manager.disconnect(experiment_id, websocket)
