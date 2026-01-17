from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


# REQUEST MODELS
class InviteRequest(BaseModel):
    """Invite user by email"""

    email: str


class JoinInviteRequest(BaseModel):
    """Join group via invite (optional extra data)"""

    token: str


# RESPONSE MODELS
class InviteResponse(BaseModel):
    """Invite result - Push vs Email"""

    status: str  # "push_sent" | "email_sent"
    email: str
    user_id: Optional[str] = None
    invite_token: Optional[str] = None
    group_name: str


class JoinInviteResponse(BaseModel):
    """Result after joining via invite"""

    status: str
    group_id: str
    role: str
    group_name: str


class PendingInviteResponse(BaseModel):
    """Single pending invite info"""

    id: str
    group_id: str
    group_name: str
    invited_by: str
    token: str
    created_at: Optional[str] = None


class PendingInvitesResponse(BaseModel):
    """List of pending invites"""

    invites: List[PendingInviteResponse]
