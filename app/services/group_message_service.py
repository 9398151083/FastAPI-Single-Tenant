from sqlalchemy.orm import Session
from app.entities.group_message import GroupMessage


class GroupMessageService:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self,
        group_id: str,
        sender_id: str,
        sender_name: str,
        message: str,
    ) -> GroupMessage:
        msg = GroupMessage(
            group_id=group_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message=message,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_group_messages(self, group_id: str, limit: int = 50):
        return (
            self.db.query(GroupMessage)
            .filter(GroupMessage.group_id == group_id)
            .order_by(GroupMessage.created_at.asc())
            .limit(limit)
            .all()
        )
