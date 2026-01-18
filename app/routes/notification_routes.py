"""✅ Notification Routes - Controllers Only"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/")
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """✅ Get user's notifications with stats"""
    service = NotificationService(db)
    return service.get_user_notifications(
        user_id=str(current_user.id), limit=limit, unread_only=unread_only
    )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """✅ Mark single notification read"""
    service = NotificationService(db)
    result = service.mark_notification_read(
        notification_id=notification_id, user_id=str(current_user.id)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")

    return result


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """✅ Mark all notifications read"""
    service = NotificationService(db)
    return service.mark_all_read(str(current_user.id))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """✅ Delete single notification"""
    service = NotificationService(db)
    if not service.delete_notification(notification_id, str(current_user.id)):
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"status": "deleted", "id": notification_id}


@router.delete("/")
async def delete_all_notifications(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """✅ Delete all notifications"""
    service = NotificationService(db)
    return service.delete_all_notifications(str(current_user.id))


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """✅ Notification statistics"""
    service = NotificationService(db)
    return service.get_stats(str(current_user.id))
