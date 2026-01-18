# Complete routes file
from fastapi import APIRouter, Depends, HTTPException
from grpc import services
from sqlalchemy.orm import Session
from typing import List
from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.task_service import TaskService
from app.models.task_models import (
    TaskCreate,
    TaskResponse,
    TaskUpdateStatus,
    TaskAssign,
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/{group_id}", response_model=TaskResponse, status_code=201)
async def create_group_task(
    group_id: str,
    task_data: TaskCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    try:
        return service.create_group_task(
            group_id, task_data.title, current_user, **task_data.dict(exclude={"title"})
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{group_id}", response_model=List[TaskResponse])
async def get_group_tasks(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    try:
        return service.get_group_tasks(group_id, current_user)
    except ValueError as e:
        raise HTTPException(403, str(e))


@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_data: TaskUpdateStatus,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    return service.update_task_status(task_id, status_data.status, current_user)


@router.get("/my", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    service = TaskService(db)
    return service.get_user_tasks(current_user)


@router.get("/{group_id}/stats")
async def get_task_stats(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    return service.get_task_stats(group_id, current_user)


# ✅ ASSIGN TASK - MISSING
@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task_endpoint(
    task_id: str,
    assign_data: TaskAssign,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    try:
        return service.assign_task(task_id, assign_data.assignee_id, current_user)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ✅ DELETE TASK - MISSING
@router.delete("/{task_id}", status_code=204)
async def delete_task_endpoint(
    task_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    try:
        service.delete_task(task_id, current_user)  # Add this method to TaskService
        return None  # 204 No Content
    except ValueError as e:
        raise HTTPException(400, str(e))


# ✅ SINGLE TASK GET - USEFUL
@router.get("/{task_id}", response_model=TaskResponse)
async def get_single_task(
    task_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    tasks = services.get_group_tasks_for_task(db, task_id, current_user)  # Implement
    if not tasks:
        raise HTTPException(404, "Task not found")
    return tasks[0]
