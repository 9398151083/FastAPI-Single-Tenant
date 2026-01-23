from sqlalchemy.orm import Session
from app.entities.chat_message import ChatMessage
from app.repositories.group_repository import is_user_in_group


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def validate_membership(self, group_id, user_id):
        if not is_user_in_group(self.db, group_id, user_id):
            raise Exception("User not in group")

    def save_message(self, group_id, user_id, message):
        chat = ChatMessage(group_id=group_id, sender_id=user_id, message=message)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat
