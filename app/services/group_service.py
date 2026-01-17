from sqlalchemy.orm import Session
import uuid
from fastapi import HTTPException

from app.entities.user import User
from app.utils.db_queries import (
    create_group,
    create_membership,
    get_user_groups,
    get_group_by_id,
    is_user_member,
    list_all_groups,
)


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, group_data: dict, current_user: User):
        """Create new group + auto-add creator as owner"""
        if len(group_data["name"]) < 3:
            raise ValueError("Group name must be at least 3 characters")

        group_id = str(uuid.uuid4())

        # 1. Create group
        create_group(self.db, group_id, group_data["name"], str(current_user.id))

        # 2. Add creator as owner ✅ FIXED - Direct call
        membership_id = str(uuid.uuid4())
        create_membership(
            self.db, membership_id, group_id, str(current_user.id), "owner"
        )

        self.db.commit()

        # 3. Return created group ✅ FIXED
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
        """Get all groups for current user"""
        groups = get_user_groups(self.db, str(current_user.id))
        return {"groups": groups}

    def join_group(self, group_id: str, current_user: User):
        """Join existing group"""
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
        print(87654)
        return {
            "status": "joined",
            "group_id": group_id,
            "role": "member",
            "group_name": group.name,
        }

    def list_all_groups(self):
        """List all groups"""
        groups = list_all_groups(self.db)
        return [{"id": g.id, "name": g.name} for g in groups]
