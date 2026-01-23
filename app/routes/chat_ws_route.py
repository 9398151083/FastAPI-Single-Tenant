from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import get_user_from_ws_token
from app.core.websocket_manager import manager
from app.services.chat_service import ChatService

router = APIRouter()


@router.websocket("/ws/groups/{group_id}")
async def group_chat(
    websocket: WebSocket,
    group_id: str,
    db: Session = Depends(get_db),
):
    user = await get_user_from_ws_token(websocket, db)

    service = ChatService(db)
    service.validate_membership(group_id, user.id)

    await manager.connect(group_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg = service.save_message(group_id, user.id, data["message"])

            await manager.broadcast(
                group_id,
                {
                    "id": str(msg.id),
                    "group_id": str(group_id),
                    "sender_id": str(user.id),
                    "message": msg.message,
                    "created_at": msg.created_at.isoformat(),
                },
            )

    except WebSocketDisconnect:
        manager.disconnect(group_id, websocket)
