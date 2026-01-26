from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.connectors.database_connector import get_db
from app.entities.user import User
from app.services.group_message_service import GroupMessageService
from app.utils.auth import verify_auth_token


router = APIRouter(prefix="/api/groups", tags=["Group Messages"])


@router.get("/{group_id}/messages")
def get_group_messages(
    group_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(verify_auth_token),
):
    service = GroupMessageService(db)
    messages = service.get_group_messages(group_id)

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender_name,
            "message": m.message,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
