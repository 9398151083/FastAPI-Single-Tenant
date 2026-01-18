from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import asyncio
from typing import List, Dict, Any
from fastapi import HTTPException

from app.entities.user import User
from app.entities.task import Task
from app.utils.db_queries import (
    create_task,
    get_group_tasks,
    get_user_group_tasks,
    get_group_by_id,
    is_user_member,
)
from app.utils.notification_utils import notify_group_members
from app.models.task_models import (
    TaskCreate,
    TaskResponse,
    TaskStatsResponse,
    TaskAssign,
)


class TaskService:
    """Complete Task Management Service with CRUD + Notifications"""

    def __init__(self, db: Session):
        self.db = db

    def create_group_task(
        self, group_id: str, title: str, current_user: User, **kwargs
    ) -> TaskResponse:
        """Create task + notify all group members (except creator)"""
        # 1. Validate group exists + user is member
        group = get_group_by_id(self.db, group_id)
        if not group:
            raise ValueError("Group not found")

        if not is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Only group members can create tasks")

        # 2. Validate input
        if len(title) < 3 or len(title) > 200:
            raise ValueError("Task title must be 3-200 characters")

        task_id = str(uuid.uuid4())

        # 3. Create task data
        task_data = {
            "id": task_id,
            "group_id": group_id,
            "title": title,
            "created_by": str(current_user.id),
            "description": kwargs.get("description"),
            "assigned_to": kwargs.get("assigned_to"),
            "status": kwargs.get("status", "pending"),
            "priority": kwargs.get("priority", "medium"),
            "due_date": kwargs.get("due_date"),
        }

        # ✅ create_task handles commit internally
        task = create_task(self.db, **task_data)
        print(f"✅ Task created: {task_id}")

        # 4. NOTIFY ALL GROUP MEMBERS (except creator) - ASYNC FIRE & FORGET
        asyncio.create_task(
            notify_group_members(
                self.db,
                group_id,
                exclude_user_id=str(current_user.id),
                message=f"New task created: {title}",
                title="📋 New Task",
                data={"task_id": task_id},
            )
        )

        # 5. Map to response
        task_response = TaskResponse(
            id=task.id,
            group_id=task.group_id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            created_by=task.created_by,
            created_at=task.created_at.isoformat(),
        )

        return task_response

    def get_group_tasks(self, group_id: str, current_user: User) -> List[TaskResponse]:
        """Get all tasks for specific group (user must be member)"""
        if not is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Access denied - not a group member")

        tasks = get_group_tasks(self.db, group_id)
        return [
            TaskResponse(
                id=task.id,
                group_id=task.group_id,
                title=task.title,
                description=task.description,
                assigned_to=task.assigned_to,
                status=task.status,
                priority=task.priority,
                due_date=task.due_date.isoformat() if task.due_date else None,
                created_by=task.created_by,
                created_at=task.created_at.isoformat(),
            )
            for task in tasks
        ]

    def get_user_tasks(self, current_user: User) -> List[TaskResponse]:
        """Get all tasks from user's groups"""
        tasks = get_user_group_tasks(self.db, str(current_user.id))
        return [
            TaskResponse(
                id=task.id,
                group_id=task.group_id,
                title=task.title,
                description=task.description,
                assigned_to=task.assigned_to,
                status=task.status,
                priority=task.priority,
                due_date=task.due_date.isoformat() if task.due_date else None,
                created_by=task.created_by,
                created_at=task.created_at.isoformat(),
            )
            for task in tasks
        ]

    def update_task_status(
        self, task_id: str, status: str, current_user: User
    ) -> TaskResponse:
        """Update task status (pending → in-progress → done)"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        # Validate group access
        if not is_user_member(self.db, task.group_id, str(current_user.id)):
            raise ValueError("Access denied")

        valid_statuses = ["pending", "in-progress", "done"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be: {valid_statuses}")

        task.status = status

        # Notify group if completed
        if status == "done":
            asyncio.create_task(
                notify_group_members(
                    self.db,
                    task.group_id,
                    message=f"Task completed: {task.title}",
                    title="✅ Task Done",
                    data={"task_id": task_id},
                )
            )

        self.db.commit()
        self.db.refresh(task)
        return TaskResponse(
            id=task.id,
            group_id=task.group_id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            created_by=task.created_by,
            created_at=task.created_at.isoformat(),
        )

    def assign_task(
        self, task_id: str, assignee_id: str, current_user: User
    ) -> TaskResponse:
        """Assign task to group member"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        # Validate permissions
        if not is_user_member(self.db, task.group_id, str(current_user.id)):
            raise ValueError("Access denied")

        # Validate assignee is group member
        if not is_user_member(self.db, task.group_id, assignee_id):
            raise ValueError("Assignee must be group member")

        task.assigned_to = assignee_id

        # Notify group members (exclude assignee)
        asyncio.create_task(
            notify_group_members(
                self.db,
                task.group_id,
                exclude_user_id=assignee_id,
                message=f"You've been assigned task: {task.title}",
                title="🎯 Task Assigned",
                data={"task_id": task_id},
            )
        )

        self.db.commit()
        self.db.refresh(task)
        return TaskResponse(
            id=task.id,
            group_id=task.group_id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            created_by=task.created_by,
            created_at=task.created_at.isoformat(),
        )

    def delete_task(self, task_id: str, current_user: User):
        """Delete task - only group members can delete"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        if not is_user_member(self.db, task.group_id, str(current_user.id)):
            raise ValueError("Access denied")

        self.db.delete(task)
        self.db.commit()
        print(f"✅ Task deleted: {task_id}")

    def get_task_stats(self, group_id: str, current_user: User) -> Dict[str, Any]:
        """Group task statistics - EFFICIENT SQL QUERY"""
        if not is_user_member(self.db, group_id, str(current_user.id)):
            raise ValueError("Access denied")

        # ✅ Efficient SQL query - NO list loading into memory
        stats = (
            self.db.query(
                func.count(Task.id).label("total"),
                func.sum(func.case((Task.status == "pending", 1), else_=0)).label(
                    "pending"
                ),
                func.sum(func.case((Task.status == "in-progress", 1), else_=0)).label(
                    "in_progress"
                ),
                func.sum(func.case((Task.status == "done", 1), else_=0)).label("done"),
            )
            .filter(Task.group_id == group_id)
            .one()
        )

        total = int(stats.total) if stats.total is not None else 0
        completion_rate = round((stats.done / total * 100), 1) if total > 0 else 0

        return {
            "total": total,
            "pending": int(stats.pending),
            "in_progress": int(stats.in_progress),
            "done": int(stats.done),
            "completion_rate": completion_rate,
        }

    def get_single_task(self, task_id: str, current_user: User) -> TaskResponse:
        """Get single task by ID"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")

        if not is_user_member(self.db, task.group_id, str(current_user.id)):
            raise ValueError("Access denied")

        return TaskResponse(
            id=task.id,
            group_id=task.group_id,
            title=task.title,
            description=task.description,
            assigned_to=task.assigned_to,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date.isoformat() if task.due_date else None,
            created_by=task.created_by,
            created_at=task.created_at.isoformat(),
        )
