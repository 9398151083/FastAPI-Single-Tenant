from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.models.task_models import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskSummary,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """Get all tasks for authenticated user"""
    service = TaskService(db)
    return service.get_user_tasks(current_user)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Create new task for authenticated user"""
    service = TaskService(db)
    return service.create_task(task, current_user)


@router.get("/summary", response_model=TaskSummary)
async def task_summary(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """Get task statistics"""
    service = TaskService(db)
    return service.get_task_summary(current_user)
