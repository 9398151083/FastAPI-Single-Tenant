"""✅ WebSocket Connection Manager - Real-time delivery"""

from typing import Dict
from fastapi import WebSocket
import json


class ConnectionManager:
    """✅ Manages WebSocket connections for instant notifications"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # user_id → WebSocket

    async def connect(self, user_id: str, websocket: WebSocket):
        """Add user to active connections"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"🔌 {user_id} connected via WebSocket")

    def disconnect(self, user_id: str):
        """Remove user from active connections"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"🔌 {user_id} disconnected")

    async def send_to_user(self, user_id: str, message: dict):
        """Send notification to specific user (if online)"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
                print(2345678)
                print(f"📱 INSTANT: {user_id} got notification")
            except Exception as e:
                print(f"❌ Failed to send to {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast_to_group(self, group_id: str, message: dict):
        """Send to all online users in group"""
        for user_id, websocket in list(self.active_connections.items()):
            await self.send_to_user(user_id, message)


# ✅ Global manager instance
notification_manager = ConnectionManager()
