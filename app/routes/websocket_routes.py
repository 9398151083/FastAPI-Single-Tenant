"""
✅ WebSocket Routes for Desktop Push Notifications + OFFLINE SUPPORT
Desktop App URL: ws://localhost:8000/ws/notifications/{user_id}
Online=Instant | Offline=DB Queue → Delivered on reconnect!
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.utils.notification_utils import NotificationManager, get_unread_notifications
from app.connectors.database_connector import get_db
import json

# ✅ Your existing router setup
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db),  # ✅ DB for offline notifications
):
    """
    ✅ DESKTOP APP CONNECTS HERE:
    ws://localhost:8000/ws/notifications/user123

    1. DELIVER missed offline notifications FIRST
    2. Connect to NotificationManager
    3. TaskService → notify_group_members() → INSTANT new notifications
    """
    await websocket.accept()

    # ✅ STEP 1: DELIVER ALL MISSED NOTIFICATIONS (Offline queue)
    print(f"📬 Checking missed notifications for {user_id}")
    missed_notifications = await get_unread_notifications(db, user_id)

    for notif in missed_notifications:
        notif_dict = {
            "id": str(notif.id),
            "group_id": notif.group_id,
            "user_id": notif.user_id,
            "title": notif.title,
            "message": notif.message,
            "data": notif.data,
            "type": notif.type,
            "timestamp": notif.created_at.isoformat(),
            "delivery_type": "missed",  # Special flag
        }
        await websocket.send_text(json.dumps(notif_dict))
        print(f"📤 SENT MISSED → {user_id[:8]}: {notif.title}")

    if missed_notifications:
        print(f"✅ Caught up {len(missed_notifications)} missed notifications")

    # ✅ STEP 2: Welcome + Connect to live notifications
    await NotificationManager.connect(websocket, user_id)

    try:
        # ✅ STEP 3: Keep connection alive (Desktop 24/7)
        while True:
            await websocket.receive_text()  # Ping/pong heartbeat
    except WebSocketDisconnect:
        print(f"🔌 {user_id} disconnected normally")
        await NotificationManager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error for {user_id}: {e}")
        await NotificationManager.disconnect(websocket)


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    """✅ Health check endpoint for desktop apps"""
    await websocket.accept()
    await websocket.send_text(
        '{"type": "pong", "status": "alive", "timestamp": "'
        + str(datetime.now().isoformat())
        + '"}'
    )
    await websocket.close()


@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    """✅ Status endpoint - returns active connections count"""
    await websocket.accept()
    await websocket.send_text(
        json.dumps(
            {
                "type": "status",
                "active_connections": len(NotificationManager.active_connections),
                "status": "healthy",
            }
        )
    )
    await websocket.close()
