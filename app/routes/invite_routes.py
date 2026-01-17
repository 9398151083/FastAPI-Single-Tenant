from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.invite_service import InviteService  # ✅ SEPARATE SERVICE
from app.models.invite_models import InviteRequest, InviteResponse

router = APIRouter(prefix="/api/invites", tags=["Invites"])


@router.post("/{group_id}", response_model=InviteResponse)  # Changed path
async def invite_user_to_group(
    group_id: str,
    invite_data: InviteRequest,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = InviteService(db)
    return service.invite_user(group_id, invite_data.email, current_user)


@router.post("/join/{token}")
async def join_group_by_invite(
    token: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = InviteService(db)
    return service.join_by_invite_token(token, current_user)


@router.get("/pending")
async def get_pending_invites(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    service = InviteService(db)
    return service.get_pending_invites(str(current_user.id))
