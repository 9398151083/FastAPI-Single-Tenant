# app/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

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
from app.core.cache import get_cache, set_cache, invalidate_cache

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

CACHE_TTL = 300  # 5 minutes
# ----------------------------------------------------


# ===================== GET: MY TASKS =====================
@router.get("/my", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"user_tasks:{current_user.id}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    tasks = TaskService(db).get_user_tasks(current_user)
    await set_cache(cache_key, json.dumps([t.dict() for t in tasks]), CACHE_TTL)
    return tasks


# ===================== GET: GROUP TASKS =====================
@router.get("/{group_id}", response_model=List[TaskResponse])
async def get_group_tasks(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"group_tasks:{group_id}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    tasks = TaskService(db).get_group_tasks(group_id, current_user)
    await set_cache(cache_key, json.dumps([t.dict() for t in tasks]), CACHE_TTL)
    return tasks


# ===================== GET: GROUP STATS =====================
@router.get("/{group_id}/stats")
async def get_task_stats(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"group_task_stats:{group_id}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    stats = TaskService(db).get_task_stats(group_id, current_user)
    await set_cache(cache_key, json.dumps(stats), CACHE_TTL)
    return stats


# ===================== GET: SINGLE TASK =====================
@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_single_task(
    task_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"task:{task_id}"

    cached = await get_cache(cache_key)
    if cached:
        return TaskResponse(**json.loads(cached))

    task = TaskService(db).get_single_task(task_id, current_user)
    if not task:
        raise HTTPException(404, "Task not found")

    await set_cache(cache_key, json.dumps(task.dict()), CACHE_TTL)
    return task


# ===================== CREATE TASK =====================
@router.post("/{group_id}", response_model=TaskResponse, status_code=201)
async def create_group_task(
    group_id: str,
    task_data: TaskCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    task = TaskService(db).create_group_task(
        group_id,
        task_data.title,
        current_user,
        **task_data.dict(exclude={"title"}),
    )

    await invalidate_cache(f"group_tasks:{group_id}")
    await invalidate_cache(f"group_task_stats:{group_id}")
    await invalidate_cache(f"user_tasks:{current_user.id}")

    return task


# ===================== UPDATE STATUS =====================
@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_data: TaskUpdateStatus,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    task = TaskService(db).update_task_status(task_id, status_data.status, current_user)

    await invalidate_cache(f"task:{task_id}")
    await invalidate_cache(f"group_tasks:{task.group_id}")
    await invalidate_cache(f"group_task_stats:{task.group_id}")
    await invalidate_cache(f"user_tasks:{current_user.id}")

    return task


# ===================== ASSIGN TASK =====================
@router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    assign_data: TaskAssign,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    task = TaskService(db).assign_task(task_id, assign_data.assignee_id, current_user)

    await invalidate_cache(f"task:{task_id}")
    await invalidate_cache(f"group_tasks:{task.group_id}")
    await invalidate_cache(f"group_task_stats:{task.group_id}")
    await invalidate_cache(f"user_tasks:{assign_data.assignee_id}")

    return task


# ===================== DELETE TASK =====================
@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    task = TaskService(db).delete_task(task_id, current_user)

    await invalidate_cache(f"task:{task_id}")
    await invalidate_cache(f"group_tasks:{task.group_id}")
    await invalidate_cache(f"group_task_stats:{task.group_id}")
    await invalidate_cache(f"user_tasks:{current_user.id}")

    return task
