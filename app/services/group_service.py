from sqlalchemy.orm import Session
import uuid
from fastapi import HTTPException

from app.entities.user import User
from app.models.group_models import GroupResponse
from app.services.notification_service import NotificationService
from app.utils.db_queries import (
    add_user_to_group,
    create_group,
    create_membership,
    get_group_members,
    get_invite_by_token,
    get_user_groups,
    get_group_by_id,
    is_user_member,
    list_all_groups,
)


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    # ✅ Expose this for WebSocket usage
    def is_member(self, group_id: str, user_id: str) -> bool:
        return is_user_member(self.db, group_id, user_id)

    def create_group(self, group_data: GroupResponse, current_user: User):
        if len(group_data.name) < 3:
            raise ValueError("Group name must be at least 3 characters")

        group_id = str(uuid.uuid4())

        create_group(self.db, group_id, group_data.name, str(current_user.id))

        membership_id = str(uuid.uuid4())
        create_membership(
            self.db, membership_id, group_id, str(current_user.id), "owner"
        )

        self.db.commit()

        created_group = get_group_by_id(self.db, group_id)

        return {
            "id": created_group.id,
            "name": created_group.name,
            "created_by": created_group.created_by,
            "created_at": (
                created_group.created_at.isoformat()
                if created_group.created_at
                else None
            ),
        }

    def get_user_groups(self, current_user: User):
        groups = get_user_groups(self.db, str(current_user.id))
        return {"groups": [GroupResponse.from_orm(g).dict() for g in groups]}

    def join_group(self, group_id: str, current_user: User):
        if is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Already a member of this group")

        group = get_group_by_id(self.db, group_id)
        if not group:
            raise ValueError("Group not found")

        membership_id = str(uuid.uuid4())
        create_membership(
            self.db, membership_id, group_id, str(current_user.id), "member"
        )
        self.db.commit()

        return {
            "status": "joined",
            "group_id": group_id,
            "role": "member",
            "group_name": group.name,
        }

    def list_all_groups(self):
        groups = list_all_groups(self.db)
        return [{"id": g.id, "name": g.name} for g in groups]

    async def join_group_with_token(
        self, group_id: str, token: str, current_user: User
    ):
        invite = get_invite_by_token(self.db, token)
        if not invite or invite.group_id != group_id:
            raise HTTPException(400, "Invalid or expired invite")

        if is_user_member(self.db, group_id, str(current_user.id)):
            raise HTTPException(400, "Already a group member")

        add_user_to_group(self.db, group_id, str(current_user.id))

        self.db.delete(invite)
        self.db.commit()

        group = get_group_by_id(self.db, group_id)
        members = get_group_members(self.db, group_id)

        notification_service = NotificationService(self.db)
        for member_id in members:
            if member_id != str(current_user.id):
                await notification_service.push_notification(
                    user_id=member_id,
                    message=f"🎉 {current_user.name} joined '{group.name}'!",
                    group_id=group_id,
                    type="group_member_joined",
                )

        return {
            "success": True,
            "message": f"✅ Joined '{group.name}'!",
            "group_id": group_id,
            "group_name": group.name,
            "members_count": len(members),
            "welcome_message": f"Welcome to {group.name}!",
        }
