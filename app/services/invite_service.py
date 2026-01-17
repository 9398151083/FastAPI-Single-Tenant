from sqlalchemy.orm import Session
import uuid
from fastapi import HTTPException

from app.entities.user import User
from app.entities.invite import Invite
from app.models.invite_models import InviteResponse
from app.utils.db_queries import (
    get_user_by_email,
    create_invite,
    get_invite_by_token,
    get_group_by_id,
    is_user_member,
    create_membership,
    accept_invite,
)
from app.utils.mailer import send_invite_email, send_otp_email


class InviteService:
    def __init__(self, db: Session):
        self.db = db

    def invite_user(self, group_id: str, email: str, current_user: User):
        """Invite logic - Push vs Email"""
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
            # ✅ EXISTING USER → Push notification
            self.queue_push_notification(
                str(user.id), f"Invited to '{group.name}' by {current_user.name}"
            )
            return {
                "status": "push_sent",
                "email": email,
                "user_id": str(user.id),
                "group_name": group.name,
            }

        else:
            email_sent = send_invite_email(email, token, group.name, group_id)
            return InviteResponse(
                status="email_sent" if email_sent else "email_failed",
                email=email,
                invite_token=token,
                group_name=group.name,
            )
            # # ✅ NEW USER → Email registration link
            # invite_link = (
            #     f"http://localhost:3000/register?token={token}&group={group_id}"
            # )
            # send_invite_email(email, invite_link, group.name)
            # return {
            #     "status": "email_sent",
            #     "email": email,
            #     "invite_token": token,
            #     "group_name": group.name,
            # }

    def join_by_invite_token(self, token: str, current_user: User):
        """Join group via invite token"""
        invite = get_invite_by_token(self.db, token)
        if not invite or invite.status != "pending":
            raise ValueError("Invalid or expired invite")

        # Auto-join user to group
        group_id = invite.group_id
        if is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Already a member of this group")

        membership_id = str(uuid.uuid4())
        create_membership(
            self.db, membership_id, group_id, str(current_user.id), "member"
        )

        # Mark invite as accepted
        accept_invite(self.db, invite.id)
        self.db.commit()

        group = get_group_by_id(self.db, group_id)
        return {
            "status": "joined",
            "group_id": group_id,
            "role": "member",
            "group_name": group.name,
        }

    def get_pending_invites(self, user_id: str):
        """Get pending invites for user - FIXED NULL CHECK"""
        # ✅ FIX: Get user first and check if exists
        user = get_user_by_email(self.db, user_id)
        if not user:
            return []  # ✅ Return empty list if user not found

        # Now safe to use user.email
        invites = (
            self.db.query(Invite)
            .filter(
                Invite.email == user.email,  # ✅ SAFE - user exists
                Invite.status == "pending",
            )
            .all()
        )

        return [
            {
                "id": invite.id,
                "group_id": invite.group_id,
                "group_name": (
                    get_group_by_id(self.db, invite.group_id).name
                    if get_group_by_id(self.db, invite.group_id)
                    else "Unknown"
                ),
                "invited_by": invite.invited_by,
                "token": invite.token,
                "created_at": (
                    invite.created_at.isoformat() if invite.created_at else None
                ),
            }
            for invite in invites
        ]

    def queue_push_notification(self, user_id: str, message: str):
        """Queue push notification (WebSocket/FCM later)"""
        print(f"🚨 PUSH: {message} → user {user_id}")
