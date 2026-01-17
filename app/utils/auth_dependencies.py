from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.connectors.database_connector import get_db
from app.entities.user import User

# Load .env and set constants
load_dotenv()
SECRET_KEY = "LYSw3EDblwQMxzu5gdgK97gidtSIx0f8JvAjEvINQXuM8Tk-fkZq1tuvpEemI88FmNQTyNi9NaHW2hrQZNLw3w"
ALGORITHM = "HS256"

security = HTTPBearer()


async def verify_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Verify JWT and return current user"""
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        # Decode JWT token (YOUR TOKEN WORKS!)
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )

        # Extract user_id (ignores extra fields like "type")
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401, detail="Invalid token payload - no user ID"
            )

        # Get user from database
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=401, detail=f"User not found: {user_id}")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account inactive")

        return user  # ✅ Returns full User object

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication service error")
