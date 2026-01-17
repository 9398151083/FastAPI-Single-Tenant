from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
import uuid


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    group_id: str = "00000000-0000-0000-0000-000000000000"
    priority: str = "medium"
    status: str = "open"
    assigned_to: str | None = None  # ✅ None, not "string"
    parent_id: str | None = None  # ✅ None, not "string"
    due_date: str | None = None


class TaskResponse(BaseModel):
    id: str
    group_id: str
    title: str
    description: str
    assigned_to: str | None
    parent_id: str | None
    priority: str
    status: str
    due_date: Optional[str | date]


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


# ✅ MISSING PIECE - Add this!
class TaskSummary(BaseModel):
    total_tasks: int
    open: int
    completed: int
