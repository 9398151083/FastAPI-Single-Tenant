from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.connectors.database_connector import get_db
from app.websocket.manager import notification_manager
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)

    # ✅ Accept & register connection (ONLY ONCE)
    await notification_manager.connect(user_id, websocket)

    # ✅ Send missed notifications once
    missed = service.get_user_notifications(user_id, unread_only=True)

    for notif in missed["notifications"]:
        await websocket.send_json(
            {
                "type": "notification",
                "delivery_type": "missed",
                **notif,
            }
        )

    try:
        # ✅ Keep connection alive WITHOUT expecting client messages
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    finally:
        notification_manager.disconnect(user_id)


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(
        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
    )
    await websocket.close()


@router.websocket("/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(
        {
            "active_connections": len(notification_manager.active_connections),
            "status": "healthy",
        }
    )
    await websocket.close()
