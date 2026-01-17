from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.connectors.database_connector import get_db
from app.utils.auth import get_current_user
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User

router = APIRouter(prefix="/api/protected", tags=["Protected"])


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "contact": current_user.contact,
        "is_verified": current_user.is_verified,
    }
