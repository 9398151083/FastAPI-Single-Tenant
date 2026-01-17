from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.connectors.database_connector import get_db
from app.entities.user import User

load_dotenv()
# ... your existing imports ...

# HARDCODED - MUST MATCH jwt.py
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
        print(122)
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Convert to UUID
        user_id_uuid = user_id  # Already str(UUID)

        # Get user from database
        user = db.get(User, user_id_uuid)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User inactive")

        return user  # ✅ Returns User object

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception:
        raise HTTPException(status_code=500, detail="Auth service error")
