from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.group_service import GroupService
from app.models.group_models import (
    GroupCreate,
    GroupResponse,
    UserGroupsResponse,
    JoinGroupResponse,
)

router = APIRouter(prefix="/api/groups", tags=["Groups"])


@router.post("/", response_model=GroupResponse, status_code=201)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Create new group"""
    try:
        service = GroupService(db)
        return service.create_group(group_data, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my", response_model=UserGroupsResponse)
async def get_user_groups(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """Get all groups for current user"""
    service = GroupService(db)
    return service.get_user_groups(current_user)


@router.post("/{group_id}/join", response_model=JoinGroupResponse)
async def join_group(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Join existing group"""
    try:
        service = GroupService(db)
        return service.join_group(group_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[dict])
async def list_all_groups(db: Session = Depends(get_db)):
    """List all available groups to join (Public)"""
    service = GroupService(db)
    return service.list_all_groups()
