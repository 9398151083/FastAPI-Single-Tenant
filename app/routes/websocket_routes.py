"""
✅ WebSocket Routes - Updated for New ConnectionManager
Desktop App: ws://localhost:8000/ws/notifications/{user_id}
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.connectors.database_connector import get_db
from app.websocket.manager import notification_manager  # ✅ NEW IMPORT
from app.services.notification_service import NotificationService  # ✅ NEW

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    ✅ PERFECT FLOW:
    1. Send missed notifications (DB)
    2. Connect to live notifications (WebSocket)
    3. Handle disconnect cleanly
    """

    await websocket.accept()
    print(f"🔌 {user_id} WebSocket CONNECTED")

    # ✅ STEP 1: DELIVER MISSED NOTIFICATIONS
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        user_id, unread_only=True
    )

    for notif in notifications["notifications"]:
        notif_dict = {
            "type": "notification",
            "id": notif["id"],
            "group_id": notif["group_id"],
            "title": notif["title"],
            "message": notif["message"],
            "data": notif["data"],
            "delivery_type": "missed",
            "timestamp": notif["created_at"],
        }
        await websocket.send_json(notif_dict)
        print(f"📤 SENT MISSED → {user_id[:8]}: {notif['title']}")

    if notifications["notifications"]:
        print(
            f"✅ Caught up {len(notifications['notifications'])} missed notifications"
        )

    # ✅ STEP 2: Connect to NotificationManager for LIVE notifications
    await notification_manager.connect(user_id, websocket)

    try:
        # ✅ STEP 3: Keep connection alive (heartbeat)
        while True:
            await websocket.receive_text()  # Ping/pong
    except WebSocketDisconnect:
        print(f"🔌 {user_id} disconnected normally")
    except Exception as e:
        print(f"❌ WebSocket error {user_id}: {e}")
    finally:
        # ✅ CLEAN DISCONNECT
        notification_manager.disconnect(user_id)


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    """✅ Health check for desktop apps"""
    await websocket.accept()
    await websocket.send_json(
        {"type": "pong", "status": "alive", "timestamp": datetime.utcnow().isoformat()}
    )
    await websocket.close()


@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    """✅ Connection stats"""
    from app.websockets.manager import notification_manager

    await websocket.accept()
    await websocket.send_json(
        {
            "type": "status",
            "active_connections": len(notification_manager.active_connections),
            "status": "healthy",
        }
    )
    await websocket.close()
