"""Task Models - DATETIME FIXED"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    model_config = {"arbitrary_types_allowed": True}  # ✅ FIXES datetime

    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    assigned_to: Optional[str] = Field(None)
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    due_date: Optional[datetime] = None  # ✅ Now works
    status: str = Field("pending", pattern="^(pending|in-progress|done)$")


class TaskUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(pending|in-progress|done)$")


class TaskAssign(BaseModel):
    assignee_id: str = Field(...)


class TaskResponse(BaseModel):

    id: str
    group_id: str
    title: str
    description: Optional[str]
    assigned_to: Optional[str]
    status: str
    priority: str
    due_date: Optional[str]  # ✅ String for API response
    created_by: str
    created_at: Optional[str]


class TaskStatsResponse(BaseModel):

    total: int
    pending: int
    in_progress: int
    done: int
    completion_rate: float = Field(..., ge=0.0, le=1.0)
