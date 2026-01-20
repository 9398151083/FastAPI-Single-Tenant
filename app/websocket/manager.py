from fastapi import WebSocket


class NotificationManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, payload: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(payload)

    async def send_to_many(self, user_ids: list[str], payload: dict):
        for user_id in user_ids:
            await self.send_to_user(user_id, payload)


notification_manager = NotificationManager()
