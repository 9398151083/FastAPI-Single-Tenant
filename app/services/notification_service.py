"""✅ Notification Service - DB + WebSocket Integration"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.entities.notifications import UserNotification
from app.websocket.manager import notification_manager  # ✅ Import manager


class NotificationService:
    """✅ Complete Notification CRUD + WebSocket Delivery"""

    def __init__(self, db: Session):
        self.db = db

    def queue_push_notifications(
        self,
        user_id: str,
        message: str,
        group_id: str = None,
        invite_token: str = None,
        data: dict = None,
        type: str = "info",
    ):

        notification_id = str(uuid.uuid4())

        # ✅ BUILD COMPLETE NOTIFICATION DATA WITH JOIN URL
        notification_data = data or {}

        # ✅ CRITICAL: Add join_url for group invites
        if type == "group_invite" and group_id and invite_token:
            notification_data = {
                "group_id": group_id,
                "invite_token": invite_token,
                "action": "join_group",
                "join_url": f"http://localhost:8000/api/groups/{group_id}/join?token={invite_token}",  # ← MISSING THIS!
            }

        # Save to DB
        notification_record = UserNotification(
            id=notification_id,
            user_id=user_id,
            group_id=group_id,
            title="Group Invite" if type == "group_invite" else "Notification",
            message=message,
            data=notification_data,  # ✅ NOW HAS join_url
            type=type,
            is_read=False,
        )
        self.db.add(notification_record)
        self.db.commit()

        # WebSocket message
        websocket_message = {
            "type": "notification",
            "id": notification_id,
            "title": notification_record.title,
            "message": message,
            "data": notification_data,  # ✅ join_url reaches frontend!
            "group_id": group_id,
            "is_read": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        notification_manager.send_to_user(user_id, websocket_message)
        print(f"🚨 SENT: {message} → {user_id} (DB+WebSocket)")
        return notification_id

    def queue_push_notification(  # ✅ ASYNC for WebSocket
        self,
        user_id: str,
        message: str,
        group_id: str = None,
        invite_token: str = None,
        data: dict = None,
        type: str = "info",
    ) -> str:
        """🚀 SAVES TO DB + SENDS VIA WEBSOCKET INSTANTLY"""
        notification_id = str(uuid.uuid4())

        # ✅ SAVE TO DB
        notification_data = UserNotification(
            id=notification_id,
            user_id=user_id,
            group_id=group_id,
            title="Group Invite" if type == "group_invite" else "Notification",
            message=message,
            data=data
            or (
                {"group_id": group_id, "invite_token": invite_token, "action": type}
                if group_id or invite_token
                else {}
            ),
            type=type,
            is_read=False,
        )
        self.db.add(notification_data)
        self.db.commit()

        # 🚀 INSTANT WebSocket delivery
        websocket_message = {
            "type": "notification",
            "id": notification_id,
            "title": notification_data.title,
            "message": message,
            "data": notification_data.data,
            "group_id": group_id,
            "is_read": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        notification_manager.send_to_user(user_id, websocket_message)

        print(f"🚨 SENT: {message} → {user_id} (DB+WebSocket)")
        return notification_id

    def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> dict:
        """✅ Get notifications + stats"""
        query = self.db.query(UserNotification).filter(
            UserNotification.user_id == user_id
        )
        if unread_only:
            query = query.filter(UserNotification.is_read == False)
        notifications = (
            query.order_by(UserNotification.created_at.desc()).limit(limit).all()
        )
        stats = self._get_stats_simple(user_id)
        return {
            "notifications": [self._notification_to_dict(n) for n in notifications],
            "stats": stats,
            "has_more": len(notifications) == limit,
            "limit": limit,
            "unread_only": unread_only,
        }

    # ✅ All your existing methods unchanged...
    def mark_notification_read(
        self, notification_id: str, user_id: str
    ) -> Dict[str, Any]:
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
        count = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.user_id == user_id, UserNotification.is_read == False
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return {"status": "all_read", "count": int(count)}

    def _get_stats_simple(self, user_id: str) -> Dict[str, int]:
        total = (
            self.db.query(func.count(UserNotification.id))
            .filter(UserNotification.user_id == user_id)
            .scalar()
            or 0
        )
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
        return {
            "id": str(notification.id),
            "user_id": notification.user_id,
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
