from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.connectors.database_connector import get_db
from app.models.token_models import TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/api/auth", tags=["Auth - Invite Registration"])


@router.post("/register-invite", response_model=TokenResponse)
async def register_with_invite(
    email: str = Form(...),
    password: str = Form(...),
    token: str = Form(...),
    group_id: str = Form(...),
    name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Register new user with invite token + auto-join group"""
    try:
        service = AuthService(db)
        result = service.register_with_invite(email, password, token, group_id, name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
