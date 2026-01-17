from sqlalchemy.orm import Session
from typing import List
from app.entities.user import User
from app.models.task_models import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskSummary,
)
from app.utils.db_queries import get_user_tasks, get_task_summary  # ✅ Functions!
import uuid
from app.entities.task import Task


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_tasks(self, current_user: User) -> TaskListResponse:
        """Get user's tasks"""
        tasks = get_user_tasks(self.db, current_user)
        return TaskListResponse(tasks=tasks, total=len(tasks))

    def create_task(self, task_data: TaskCreate, current_user: User) -> TaskResponse:
        """Create task - SAFE UUID handling"""
        if len(task_data.title) < 3:
            raise ValueError("Title must be at least 3 characters")

        db_task = Task(
            id=str(uuid.uuid4()),
            group_id="7e976007-4ae7-46fd-b497-dea41385787c",
            title=task_data.title[:200],
            description=task_data.description or "",
            assigned_to=str(current_user.id),
            parent_id=None,
            priority=task_data.priority or "medium",
            status=task_data.status or "open",
            due_date=None,
        )

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task

    def get_task_summary(self, current_user: User) -> TaskSummary:
        """Get task statistics"""
        return get_task_summary(self.db, current_user)
