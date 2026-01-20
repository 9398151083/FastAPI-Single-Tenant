from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


# REQUEST MODELS
class GroupCreate(BaseModel):
    """Create new group request"""

    name: str


class JoinGroupRequest(BaseModel):
    """Join group request (if needed)"""

    group_id: str


# RESPONSE MODELS
class GroupResponse(BaseModel):
    """Single group response"""

    id: str
    name: str
    created_by: str
    created_at: Optional[str] = None


class GroupListResponse(BaseModel):
    """List of groups for public view"""

    id: str
    name: str


class UserGroupsResponse(BaseModel):
    """User's groups with role info"""

    groups: List[dict]  # [{"id": "...", "name": "...", "role": "owner"}]


class JoinGroupResponse(BaseModel):
    """Response after joining group"""

    status: str
    group_id: str
    role: str
    group_name: str


# UPDATE MODELS (Future use)
class GroupUpdate(BaseModel):
    """Update group details"""

    name: Optional[str] = None


class MembershipResponse(BaseModel):
    """Single membership info"""

    group_id: str
    user_id: str
    role: str
    joined_at: Optional[str] = None


from pydantic import BaseModel
from typing import Optional


class GroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None  # ✅ MUST be optional

    class Config:
        from_attributes = True


class UserGroupsResponse(BaseModel):
    groups: list[GroupResponse]
