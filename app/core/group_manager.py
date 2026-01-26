from typing import Dict, List
from fastapi import WebSocket
from starlette.websockets import WebSocketState


class GroupChatManager:
    def __init__(self):
        self.groups: Dict[str, List[WebSocket]] = {}

    async def connect(self, group_id: str, websocket: WebSocket):
        # ❌ DO NOT ACCEPT HERE
        self.groups.setdefault(group_id, []).append(websocket)

    def disconnect(self, group_id: str, websocket: WebSocket):
        if group_id in self.groups and websocket in self.groups[group_id]:
            self.groups[group_id].remove(websocket)

            if not self.groups[group_id]:
                del self.groups[group_id]

    async def broadcast(self, group_id: str, message: dict):
        if group_id not in self.groups:
            return

        dead_sockets: List[WebSocket] = []

        for ws in self.groups[group_id]:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(message)
                else:
                    dead_sockets.append(ws)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            self.disconnect(group_id, ws)


group_chat_manager = GroupChatManager()
