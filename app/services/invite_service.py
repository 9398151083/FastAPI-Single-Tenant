"""✅ InviteService - Push for Existing Users + FIXED get_pending_invites"""

from sqlalchemy.orm import Session
import uuid
from fastapi import HTTPException
from sqlalchemy import and_
from app.entities.user import User
from app.entities.invite import Invite
from app.entities.group import Group  # Add this import
from app.utils.db_queries import (
    get_user_by_email,
    create_invite,
    get_invite_by_token,
    get_group_by_id,
    is_user_member,
    create_membership,
    accept_invite,
)
from app.utils.mailer import send_invite_email
from app.services.notification_service import NotificationService  # ✅ Add this


class InviteService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)  # ✅ Notification service

    def invite_user(self, group_id: str, email: str, current_user: User):
        """✅ PERFECT FLOW: Existing → Push, New → Email"""
        # Check group exists + user is owner/member
        group = get_group_by_id(self.db, group_id)
        if not group:
            raise ValueError("Group not found")

        if not is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Only group members can invite")

        # Check if already member
        user = get_user_by_email(self.db, email)
        if user and is_user_member(self.db, group_id, str(user.id)):
            raise ValueError("User already in group")

        # Create invite
        token = str(uuid.uuid4())
        invite_id = str(uuid.uuid4())
        create_invite(self.db, invite_id, group_id, email, str(current_user.id), token)

        if user:
            # ✅ EXISTING USER → INSTANT PUSH NOTIFICATION
            self.notification_service.queue_push_notifications(
                str(user.id),
                f"📧 {current_user.name} invited you to '{group.name}'",
                group_id=group_id,
                invite_token=token,
                type="group_invite",
            )
            self.db.commit()
            return {
                "status": "push_sent",
                "email": email,
                "user_id": str(user.id),
                "group_name": group.name,
            }
        else:
            # ✅ NEW USER → Email registration link
            email_sent = send_invite_email(email, token, group.name, group_id)
            self.db.commit()
            return {
                "status": "email_sent" if email_sent else "email_failed",
                "email": email,
                "invite_token": token,
                "group_name": group.name,
            }

    def join_by_invite_token(self, token: str, current_user: User):
        """Join group via invite token"""
        invite = get_invite_by_token(self.db, token)
        if not invite or invite.status != "pending":
            raise ValueError("Invalid or expired invite")

        group_id = invite.group_id
        if is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Already a member of this group")

        membership_id = str(uuid.uuid4())
        create_membership(
            self.db, membership_id, group_id, str(current_user.id), "member"
        )
        accept_invite(self.db, invite.id)
        self.db.commit()

        group = get_group_by_id(self.db, group_id)
        return {
            "status": "joined",
            "group_id": group_id,
            "role": "member",
            "group_name": group.name,
        }

    def get_pending_invites(self, user_id: str):  # ✅ FIXED: user_id not email
        """✅ FIXED: Query by user_id, not email"""
        invites = (
            self.db.query(Invite)
            .filter(
                and_(
                    Invite.invited_by == user_id,  # ✅ Invites SENT BY this user
                    Invite.status == "pending",
                )
            )
            .all()
        )

        return [
            {
                "id": str(invite.id),
                "group_id": invite.group_id,
                "group_name": (
                    self.db.query(Group)
                    .filter(Group.id == invite.group_id)
                    .first()
                    .name
                    if self.db.query(Group).filter(Group.id == invite.group_id).first()
                    else "Unknown"
                ),
                "email": invite.email,
                "token": invite.token,
                "created_at": (
                    invite.created_at.isoformat() if invite.created_at else None
                ),
            }
            for invite in invites
        ]
