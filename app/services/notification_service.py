"""✅ Notification Service - Invite Support + Production Ready"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Dict, Any, List
from datetime import datetime
import uuid

from app.entities.notifications import UserNotification

# Remove Pydantic imports - pure dict responses


class NotificationService:
    """✅ Complete Notification CRUD + Invite Support"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> dict:
        """✅ Get notifications + stats - Pure dict"""
        query = self.db.query(UserNotification).filter(
            UserNotification.user_id == user_id
        )

        if unread_only:
            query = query.filter(UserNotification.is_read == False)

        notifications = (
            query.order_by(UserNotification.created_at.desc()).limit(limit).all()
        )

        stats = self._get_stats_simple(user_id)  # ✅ Use simple version

        return {
            "notifications": [self._notification_to_dict(n) for n in notifications],
            "stats": stats,
            "has_more": len(notifications) == limit,
            "limit": limit,
            "unread_only": unread_only,
        }

    def queue_push_notification(
        self,
        user_id: str,
        message: str,
        group_id: str = None,
        invite_token: str = None,
        type: str = "info",
    ) -> str:
        """✅ NEW: Queue notification (WebSocket + DB fallback)"""
        notification_id = str(uuid.uuid4())

        # Save to DB for offline users
        notification_data = UserNotification(
            id=notification_id,
            user_id=user_id,
            group_id=group_id,
            title="Group Invite" if type == "group_invite" else "Notification",
            message=message,
            data=(
                {"group_id": group_id, "invite_token": invite_token, "action": type}
                if group_id or invite_token
                else {}
            ),
            type=type,
            is_read=False,
        )
        self.db.add(notification_data)
        self.db.commit()

        print(f"🚨 PUSH QUEUED: {message} → user {user_id} (type: {type})")
        return notification_id

    def mark_notification_read(
        self, notification_id: str, user_id: str
    ) -> Dict[str, Any]:
        """✅ Mark single notification read"""
        notif = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
            .first()
        )

        if notif:
            notif.is_read = True
            self.db.commit()
            return {"status": "read", "id": notification_id, "title": notif.title}
        return None

    def mark_all_read(self, user_id: str) -> Dict[str, Any]:
        """✅ Mark all notifications read"""
        count = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.user_id == user_id, UserNotification.is_read == False
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return {"status": "all_read", "count": int(count)}

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """✅ Delete single notification"""
        result = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
            .delete()
        )
        if result > 0:
            self.db.commit()
            return True
        return False

    def delete_all_notifications(self, user_id: str) -> Dict[str, Any]:
        """✅ Delete all user notifications"""
        count = (
            self.db.query(UserNotification)
            .filter(UserNotification.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return {"status": "all_deleted", "count": int(count)}

    def _get_stats_simple(self, user_id: str) -> Dict[str, int]:
        """✅ ULTRA SIMPLE - 2 COUNT queries (NO case issues)"""
        # Total count
        total = (
            self.db.query(func.count(UserNotification.id))
            .filter(UserNotification.user_id == user_id)
            .scalar()
            or 0
        )

        # Unread count
        unread = (
            self.db.query(func.count(UserNotification.id))
            .filter(
                UserNotification.user_id == user_id, UserNotification.is_read == False
            )
            .scalar()
            or 0
        )

        return {"total": int(total), "unread": int(unread), "read": int(total - unread)}

    def _notification_to_dict(self, notification: UserNotification) -> Dict[str, Any]:
        """✅ Complete notification dict with user_id"""
        return {
            "id": str(notification.id),
            "user_id": notification.user_id,  # ✅ REQUIRED
            "group_id": notification.group_id,
            "title": notification.title,
            "message": notification.message,
            "data": notification.data or {},
            "type": notification.type,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat() if notification.created_at else None
            ),
        }
