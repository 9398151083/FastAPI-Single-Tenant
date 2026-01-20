from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import json

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
from app.core.cache import get_cache, set_cache, invalidate_cache

router = APIRouter(prefix="/api/groups", tags=["Groups"])

CACHE_TTL = 300  # 5 minutes


# ==================================================
# ✅ CREATE GROUP (NO CACHE)
# ==================================================
@router.post("/", response_model=GroupResponse, status_code=201)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Create new group"""
    try:
        service = GroupService(db)
        group = service.create_group(group_data, current_user)

        # 🔥 Invalidate public + user group lists
        await invalidate_cache("groups:all")
        await invalidate_cache(f"user_groups:{current_user.id}")

        return group
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================================================
# ✅ GET MY GROUPS (CACHED)
# ==================================================
@router.get("/my", response_model=UserGroupsResponse)
async def get_user_groups(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"user_groups:{current_user.id}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = GroupService(db)
    result = service.get_user_groups(current_user)

    await set_cache(cache_key, json.dumps(result), CACHE_TTL)
    return result


# ==================================================
# ✅ JOIN GROUP (NO CACHE)
# ==================================================
@router.post("/{group_id}/join", response_model=JoinGroupResponse)
async def join_group(
    group_id: str,
    token: str = Query(..., description="Invite token from notification"),
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Join group via invite token"""
    try:
        service = GroupService(db)
        result = await service.join_group_with_token(group_id, token, current_user)

        # 🔥 Invalidate affected caches
        await invalidate_cache(f"user_groups:{current_user.id}")
        await invalidate_cache("groups:all")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise


# ==================================================
# ✅ LIST ALL GROUPS (PUBLIC, CACHED)
# ==================================================
@router.get("/", response_model=list[dict])
async def list_all_groups(db: Session = Depends(get_db)):
    """List all available groups to join (Public)"""
    cache_key = "groups:all"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = GroupService(db)
    groups = service.list_all_groups()

    await set_cache(cache_key, json.dumps(groups), CACHE_TTL)
    return groups
