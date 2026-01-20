"""✅ Notification Routes - Controllers Only"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.notification_service import NotificationService

from app.core.cache import get_cache, set_cache, invalidate_cache, CACHE_TTL

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ============================
# ✅ GET NOTIFICATIONS (CACHED)
# ============================
@router.get("/")
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"notifications:list:{current_user.id}:{limit}:{unread_only}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = NotificationService(db)
    data = service.get_user_notifications(
        user_id=str(current_user.id),
        limit=limit,
        unread_only=unread_only,
    )

    await set_cache(cache_key, json.dumps(data), ttl=CACHE_TTL)
    return data


# ============================
# ❌ MARK SINGLE READ (NO CACHE)
# ============================
@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    result = service.mark_notification_read(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")

    # 🔥 Invalidate related caches
    await invalidate_cache(f"notifications:*:{current_user.id}*")

    return result


# ============================
# ❌ MARK ALL READ (NO CACHE)
# ============================
@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    result = service.mark_all_read(str(current_user.id))

    # 🔥 Invalidate all notification caches
    await invalidate_cache(f"notifications:*:{current_user.id}*")

    return result


# ============================
# ❌ DELETE SINGLE (NO CACHE)
# ============================
@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    if not service.delete_notification(notification_id, str(current_user.id)):
        raise HTTPException(status_code=404, detail="Notification not found")

    # 🔥 Invalidate caches
    await invalidate_cache(f"notifications:*:{current_user.id}*")

    return {"status": "deleted", "id": notification_id}


# ============================
# ❌ DELETE ALL (NO CACHE)
# ============================
@router.delete("/")
async def delete_all_notifications(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = NotificationService(db)
    result = service.delete_all_notifications(str(current_user.id))

    # 🔥 Invalidate caches
    await invalidate_cache(f"notifications:*:{current_user.id}*")

    return result


# ============================
# ✅ STATS (CACHED)
# ============================
@router.get("/stats")
async def get_stats(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"notifications:stats:{current_user.id}"

    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = NotificationService(db)
    data = service.get_stats(str(current_user.id))

    await set_cache(cache_key, json.dumps(data), ttl=CACHE_TTL)
    return data
