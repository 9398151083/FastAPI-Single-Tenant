"""✅ Notification Pydantic Models for API Responses"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationBase(BaseModel):
    group_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    message: Optional[str] = Field(None, max_length=1000)
    data: Optional[Dict[str, Any]] = {}
    type: str = Field(..., max_length=50)


class NotificationCreate(NotificationBase):
    user_id: str
    group_id: Optional[str] = None


class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    total: int
    unread: int
    read: int


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread: int
    has_more: bool
