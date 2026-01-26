from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.connectors.database_connector import get_db
from app.core.group_manager import group_chat_manager
from app.services.group_service import GroupService
from app.services.group_message_service import GroupMessageService
from app.utils.auth_dependencies import get_user_from_ws_token
from app.websocket.manager import notification_manager
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/ws", tags=["WebSocket"])


# ===================== NOTIFICATIONS =====================


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: str,
    db: Session = Depends(get_db),
):
    service = NotificationService(db)

    await notification_manager.connect(user_id, websocket)

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
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    finally:
        notification_manager.disconnect(user_id)


# ===================== PING =====================


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(
        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
    )
    await websocket.close()


# ===================== STATUS =====================


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


# ===================== GROUP CHAT =====================


@router.websocket("/groups/{group_id}")
async def websocket_group_chat(websocket: WebSocket, group_id: str):
    await websocket.accept()  # ✅ ACCEPT ONLY ONCE

    db: Session = next(get_db())

    try:
        print("WS CONNECTED:", group_id)

        # 🔐 Authenticate
        user = await get_user_from_ws_token(websocket, db)

        # 🔒 Check membership
        group_service = GroupService(db)
        if not group_service.is_member(group_id, str(user.id)):
            await websocket.send_json(
                {"type": "error", "message": "You are not a member of this group"}
            )
            await websocket.close(code=4403)
            return

        # ✅ Register connection
        await group_chat_manager.connect(group_id, websocket)

        # 🔔 Join message
        await group_chat_manager.broadcast(
            group_id,
            {"type": "system", "message": f"{user.name} joined the group"},
        )

        message_service = GroupMessageService(db)

        while True:
            data = await websocket.receive_json()
            text = data.get("message")

            if not text:
                continue

            # ✅ SAVE TO DB FIRST
            msg = message_service.save_message(
                group_id=group_id,
                sender_id=str(user.id),
                sender_name=user.name,
                message=text,
            )

            # ✅ THEN BROADCAST
            await group_chat_manager.broadcast(
                group_id,
                {
                    "type": "message",
                    "id": msg.id,
                    "from_user_id": msg.sender_id,
                    "from_name": msg.sender_name,
                    "message": msg.message,
                    "created_at": msg.created_at.isoformat(),
                },
            )

    except WebSocketDisconnect:
        group_chat_manager.disconnect(group_id, websocket)

        await group_chat_manager.broadcast(
            group_id,
            {"type": "system", "message": f"{user.name} left the group"},
        )

    finally:
        db.close()
        print("WS DISCONNECTED:", group_id)
