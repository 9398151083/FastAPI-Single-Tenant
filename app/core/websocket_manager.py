from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, group_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(group_id, set()).add(websocket)

    def disconnect(self, group_id: str, websocket: WebSocket):
        self.active_connections[group_id].discard(websocket)

    async def broadcast(self, group_id: str, message: dict):
        for ws in self.active_connections.get(group_id, []):
            await ws.send_json(message)


manager = ConnectionManager()
