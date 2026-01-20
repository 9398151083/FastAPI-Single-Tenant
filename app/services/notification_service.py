from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime
import uuid

from app.entities.notifications import UserNotification
from app.websocket.manager import notification_manager


class NotificationService:
    """✅ Notification CRUD + WebSocket Delivery"""

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # 🔔 PUSH NOTIFICATION (ASYNC + WEBSOCKET)
    # ==================================================
    async def push_notification(
        self,
        user_id: str,
        message: str,
        group_id: str = None,
        invite_token: str = None,
        data: dict = None,
        type: str = "info",
    ) -> str:
        notification_id = str(uuid.uuid4())
        payload = data or {}

        # ✅ Group invite payload
        if type == "group_invite" and group_id and invite_token:
            payload = {
                "group_id": group_id,
                "invite_token": invite_token,
                "action": "join_group",
                "join_url": f"http://localhost:8000/api/groups/{group_id}/join?token={invite_token}",
            }

        record = UserNotification(
            id=notification_id,
            user_id=user_id,
            group_id=group_id,
            title="Group Invite" if type == "group_invite" else "Notification",
            message=message,
            data=payload,
            type=type,
            is_read=False,
        )

        self.db.add(record)
        self.db.commit()

        # 🚀 Instant WebSocket delivery
        await notification_manager.send_to_user(
            user_id,
            {
                "type": "notification",
                "id": notification_id,
                "title": record.title,
                "message": message,
                "data": payload,
                "group_id": group_id,
                "is_read": False,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return notification_id

    # ==================================================
    # 📥 GET USER NOTIFICATIONS
    # ==================================================
    def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> dict:
        query = self.db.query(UserNotification).filter(
            UserNotification.user_id == user_id
        )

        if unread_only:
            query = query.filter(UserNotification.is_read == False)

        notifications = (
            query.order_by(UserNotification.created_at.desc()).limit(limit).all()
        )

        return {
            "notifications": [self._to_dict(n) for n in notifications],
            "stats": self._get_stats(user_id),
            "has_more": len(notifications) == limit,
        }

    # ==================================================
    # ✅ MARK SINGLE READ
    # ==================================================
    def mark_notification_read(self, notification_id: str, user_id: str):
        notif = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
            .first()
        )

        if not notif:
            return None

        notif.is_read = True
        self.db.commit()
        return {"status": "read"}

    # ==================================================
    # ✅ MARK ALL READ
    # ==================================================
    def mark_all_read(self, user_id: str):
        count = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False,
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return {"count": count}

    # ==================================================
    # ❌ DELETE SINGLE NOTIFICATION
    # ==================================================
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        notif = (
            self.db.query(UserNotification)
            .filter(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
            .first()
        )

        if not notif:
            return False

        self.db.delete(notif)
        self.db.commit()
        return True

    # ==================================================
    # ❌ DELETE ALL NOTIFICATIONS
    # ==================================================
    def delete_all_notifications(self, user_id: str):
        count = (
            self.db.query(UserNotification)
            .filter(UserNotification.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return {"deleted": count}

    # ==================================================
    # 📊 GET STATS (PUBLIC)
    # ==================================================
    def get_stats(self, user_id: str) -> Dict[str, int]:
        return self._get_stats(user_id)

    # ==================================================
    # 🔢 INTERNAL STATS HELPER
    # ==================================================
    def _get_stats(self, user_id: str) -> Dict[str, int]:
        total = (
            self.db.query(func.count(UserNotification.id))
            .filter(UserNotification.user_id == user_id)
            .scalar()
            or 0
        )

        unread = (
            self.db.query(func.count(UserNotification.id))
            .filter(
                UserNotification.user_id == user_id,
                UserNotification.is_read == False,
            )
            .scalar()
            or 0
        )

        return {
            "total": total,
            "unread": unread,
            "read": total - unread,
        }

    # ==================================================
    # 🔁 SERIALIZER
    # ==================================================
    def _to_dict(self, n: UserNotification) -> Dict[str, Any]:
        return {
            "id": n.id,
            "user_id": n.user_id,
            "group_id": n.group_id,
            "title": n.title,
            "message": n.message,
            "data": n.data or {},
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
